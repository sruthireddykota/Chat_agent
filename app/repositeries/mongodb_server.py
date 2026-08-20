from pymongo import DESCENDING, AsyncMongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from datetime import datetime, timezone, timedelta
from app.utils.logger import get_logger
from app.config.settings import settings
from app.models.mongo import (MongoStoreMessage,MongoDocumentData, MongoUser, UserDetails)
from app.models.workflow import WorkflowBuilder

logger=get_logger()

class MongoStore:
    def __init__(self):
        self._MONGO_URI =settings.MONGODB_URI
        self._MONGODB_DB =settings.MONGODB_DB
        self.KM_DB=settings.MONGODB_KM_DB
        self.USERS_DB=settings.MONGODB_USER_DB
    
        self.client = AsyncMongoClient(self._MONGO_URI, serverSelectionTimeoutMS=3000)
        
        self.db = self.client[self._MONGODB_DB]
        self.km_db=self.client[self.KM_DB]
        self.users_db=self.client[self.USERS_DB]
        
        self.rag_logs = self.db["rag_logs"]
        self.sessions = self.db["sessions"]
        self.messages = self.db["chatmessages"]
        self.conversation = self.db["conversation"]
        self.workflows = self.db["workflows"]
        self.documents=self.km_db["documents"]
        self.users=self.users_db["users"]
    
    def close(self):
        try:
            self.client.close()
            logger.info("[MonogoDB] connection closed successfully.")
        except Exception as e:
            logger.error("[MonogoDB] Error closing connection: %s", e)

    async def connect(self):
        try:
            await self.client.admin.command("ping")
            await self._create_index()

            logger.info("Connected to MongoDB")

        except ConnectionFailure as e:
            logger.error("MongoDB connection failed: %s", e)
            raise

    async def _create_index(self):        
        await self.sessions.create_index([("session_id", 1)], unique=True)
        await self.sessions.create_index([("user_id", 1), ("updated_at", DESCENDING)])
        await self.sessions.create_index([("user_id", 1), ("message_count", DESCENDING)])
        await self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        await self.rag_logs.create_index([("session_id", 1), ("timestamp", 1)])
        await self.workflows.create_index([("creator_id", 1), ("updated_timestamp", DESCENDING)])
        await self.workflows.create_index([("id", 1), ("creator_id", 1)], unique=True)
        
    async def create_title(self, content):
        from app.azure_clients.title_azure_client import get_client
        logger.info("Generating title for content preview: %s", content.strip()[:50])
        client = await get_client()
        content_preview = content.strip()[:200]
        response = await client.chat.completions.create(
            model=settings.AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "create a title in 2-3 words from the content"},
                {"role": "user", "content": content_preview}
            ],
            max_tokens=20
        )
        title=response.choices[0].message.content
        title = title.strip().strip('"').strip("'")
        logger.info("Generated title: %s", title)
        return title
        
        
    async def create_session(self, session_id: str, user_id: str):
        try:
            result = await self.sessions.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "title": "New Chat",
                "message_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            return str(result.inserted_id)
        except Exception as e:
            return None

    async def get_sessions(self, user_id: str, limit: int = 10):
        try:
            sessions = self.sessions.find({'user_id': user_id}).sort("updated_at", DESCENDING).limit(limit)
            result = []
            async for session in sessions:
                session["_id"] = str(session["_id"])
                result.append(session)

            return result
        except Exception as e:
            return None

    async def get_session_owner(self, session_id: str):
        try:
            session = await self.sessions.find_one({"session_id": session_id}, {"user_id": 1})
            return session.get("user_id") if session else None
        except Exception:
            return None
    
    async def delete_session(self, session_id):
        try:
            result = await self.messages.delete_many({"session_id": session_id})
            if result:
                output = await self.sessions.delete_one({"session_id": session_id})
            
            logger.info(f"Deleted session_id: {session_id}, messages_deleted: {result.deleted_count}, session_deleted: {output.deleted_count if result else 0}")
            return output.deleted_count > 0
        except Exception as e:
            return None
    
    async def get_chat_history(self, session_id: str, limit: int = 10):
        try:
            messages = (
                self.messages
                .find({'session_id': session_id})
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            result = []
            async for message in messages:
                message["_id"] = str(message["_id"])
                result.append(message)
            result.reverse()  
            return result
        except Exception as e:
            return None

    async def save_message(self, message: MongoStoreMessage) -> str:
        try:
            timestamp = message.get("timestamp") or datetime.now(timezone.utc).isoformat()

            result = await self.messages.insert_one({
                "session_id": message["session_id"],
                "role": message["role"],
                "content": message["content"],
                "timestamp": timestamp,
                "sources": message["sources"],
                "agent_name": message["agent_name"],
                "user_id": message["user_id"]
            })
            
            await self.sessions.update_one(
                {"session_id": message.get("session_id")},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                })
            
            
            if message.get("role") == "user":
                session_output = await self.sessions.find_one({'session_id': message.get("session_id")})
                if session_output is not None:

                    count = session_output.get("message_count")
                    if count == 1:
                        content = message.get("content")
                        
                        if content and content.strip():
                            try:
                                title = await self.create_title(content)  
                                if not isinstance(title, str):
                                    title = str(title) if title else "New Chat"
                                logger.info("Generated title: %s", title)
                                title = title.strip()[:50]
                                
                            except Exception as e:
                                logger.error("Error generating title: %s", e)
                                title = "New Chat"
                        else:
                            logger.info("Content is empty or whitespace. Using default title.")
                            title = "New Chat"
                            
                        await self.sessions.update_one(
                            {"session_id": message.get("session_id")},
                            {
                                "$set": {"title": title, "updated_at": datetime.now(timezone.utc).isoformat()}
                            }
                        )

            logger.info(f"Saved message for session_id: {message.get('session_id')}, role: {message.get('role')}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            return None

    async def clear_chatmessages(self, session_id):
        try:
            result = await self.messages.delete_many({"session_id": session_id})
            
            await self.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {"message_count": 0, "updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            logger.info(f"Cleared chat messages for session_id: {session_id}, deleted_count: {result.deleted_count}")
            return result.deleted_count
        
        except Exception as e:
            return None
    

    async def store_documents(self, document_data: MongoDocumentData):
        try:
            await self.documents.insert_one({
                "document_name": document_data.document_name,
                "document_id": document_data.document_id,
                "document_type": document_data.document_type,
                "timestamp": document_data.timestamp,
                "chunk_count": document_data.chunk_count,
                "uploaded_by": document_data.uploaded_by,
                "tags": document_data.tags
            })
            return True
        
        except Exception as e:
            logger.error("Error storing document: %s", e)
            return False
        
    async def delete_document(self,document_id):
        try:
            response = await self.documents.delete_one({
                "document_id":document_id
            })
            return response.deleted_count > 0 
        
        except Exception as e:
            return False
    
    async def get_documents(self):
        try:
            response = self.documents.find().sort("timestamp",1)
            
            result = []
            async for message in response:
                message["_id"] = str(message["_id"])
                result.append(message)

            return result
        except Exception as e:
            return None
    
    async def create_user(self,user_data : MongoUser):
        try:
            data={
                "username":user_data.get("username"),
                "user_id":user_data.get("user_id"),
                "password":user_data.get("password"),
                "email_id":user_data.get("email_id"),
                "created_at":datetime.now(timezone.utc).isoformat(),
                "logged_in":user_data.get("logged_in"),
                "last_logged_in":user_data.get("last_logged_in"),
                "role":"user"
            }
            response = await self.users.find_one({
                "username":user_data.get("username")
            })
            if response is not None:
                return {
                    'status':"Fail",
                    'message':'Username already Exists'
                }
            
            else:
                response = await self.users.find_one({
                "email_id":user_data.get("email_id")
                })
                if response is not None:
                    return {
                    'status':"Fail",
                    'message':'Email ID already Exists'
                }
                else:
                    await self.users.insert_one(data)
                    return {
                    'status':"success",
                    'message':'Sign up Successful!'
                }
                
        except Exception as e:
            return {
                    'status':"Error",
                    'message': f'Error:{e}'
                }
    
    async def update_user_status(self, user_id, logged_in):
        try:
            if logged_in:
                result = await self.users.update_one({"user_id": user_id}, {"$set": {"logged_in": logged_in, "last_logged_in": datetime.now(timezone.utc).isoformat()}})
            else:
                result = await self.users.update_one({"user_id": user_id}, {"$set": {"logged_in": logged_in}})
            if result.matched_count == 0:
                return None
            return True
        
        except Exception as e:
            logger.error("Error updating user status: %s", e)
            return None

    async def logout_stale_users(self, max_age_minutes: int = 30) -> int:
        """Log out users whose active login is older than the allowed age."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)).isoformat()
            result = await self.users.update_many(
                {
                    "logged_in": True,
                    "last_logged_in": {"$lte": cutoff},
                },
                {"$set": {"logged_in": False}},
            )
            return result.modified_count
        except Exception as e:
            logger.error("Error logging out stale users: %s", e, exc_info=True)
            return 0
    
    async def get_user_details(self,email_id) -> UserDetails:
        try:
            result = await self.users.find_one({
                "email_id":email_id
            })

            if result is None:
                return None

            user_details={
                "username":result.get("username"),
                "password":result.get("password"),
                "user_id":result.get("user_id"),
                "email_id":result.get("email_id"),
                "logged_in":result.get("logged_in")
                ,"role":result.get("role", "user")
            }
            return user_details
            
        except Exception as e:
            return None
    
    async def get_login_details(self,email_id):
        try:

            response = await self.users.find_one({
                "email_id":email_id
            })

            if response is None:
                return None 
            
            user = response
            logged_in = user.get("logged_in")
            last_logged_in = user.get("last_logged_in")

            if logged_in and last_logged_in:
                last_login_time = datetime.fromisoformat(last_logged_in)
                time_duration=datetime.now(timezone.utc)-last_login_time
                if time_duration.total_seconds() >= 30 * 60:
                    await self.users.update_one(
                        {"email_id":email_id},
                        {"$set":{"logged_in":False}}
                        )
                    logged_in=False
            return{
                "username": user.get("username"),
                "user_id": user.get("user_id"),
                "email_id": user.get("email_id"),
                "logged_in": logged_in,
                "last_logged_in": last_logged_in
                
            }
        except Exception as e:
            return None

    async def save_rag_log(self, session_id, query, context, answer):
        try:
            await self.rag_logs.insert_one({
                "session_id": session_id,
                "query": query,
                "context": context,    
                "answer": answer,         
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Saved RAG log for session_id: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save RAG log: {e}")
    
    async def get_average_metrics(self):
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_answer_relevance":  {"$avg": "$answer_relevance"},
                        "avg_context_relevance": {"$avg": "$context_relevance"},
                        "avg_groundedness":      {"$avg": "$groundedness"},
                        "total_evaluations":     {"$sum": 1}
                    }
                }
            ]
            
            collection = self.db[settings.MONGODB_COLLECTION]
            result =  []
            cursor= await collection.aggregate(pipeline)
            async for row in cursor:
                result.append(row)
            
            if not result:
                return {
                    "avg_answer_relevance":  None,
                    "avg_context_relevance": None,
                    "avg_groundedness":      None,
                    "total_evaluations":     0
                }
            
            row = result[0]
            return {
                "avg_answer_relevance":  round(row["avg_answer_relevance"],  3) if row["avg_answer_relevance"]  is not None else None,
                "avg_context_relevance": round(row["avg_context_relevance"], 3) if row["avg_context_relevance"] is not None else None,
                "avg_groundedness":      round(row["avg_groundedness"],      3) if row["avg_groundedness"]      is not None else None,
                "total_evaluations":     row["total_evaluations"]
            }
            
        except Exception as e:
            return None

### Conversation
    async def get_conversation_count(self, session_id: str) -> int:
        try:
            return await self.conversation.count_documents({"session_id": session_id})
        except Exception as e:
            logger.error(f"Error counting conversation messages: {e}", exc_info=True)
            return 0

    async def get_conversation_messages(self, session_id: str, limit: int = 10):
        try:
            cursor = (
                self.conversation
                .find({"session_id": session_id})
                .sort("timestamp", DESCENDING)
                .limit(max(1, limit))
            )
            result = []
            async for message in cursor:
                result.append({
                    "role": message.get("role", "unknown"),
                    "content": message.get("content", ""),
                    "agent_name": message.get("agent_name", "unknown"),
                })
            result.reverse()
            return result
        except Exception as e:
            logger.error(f"Error retrieving conversation messages: {e}", exc_info=True)
            return None
        
    async def save_conversation_message(self, message: dict) -> str:
        try:
            timestamp = message.get("timestamp") or datetime.now(timezone.utc).isoformat()
            result = await self.conversation.insert_one({
                        "session_id": message["session_id"],
                        "role": message["role"],
                        "content": message["content"],
                        "timestamp": timestamp,
                        "sources": message["sources"],
                        "agent_name": message["agent_name"],
                        "user_id": message["user_id"]
                    })
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}", exc_info=True)
            return None
        
    async def replace_with_summary(self, session_id: str, summary_text: str) -> str:
        try:
            await self.conversation.delete_many({"session_id": session_id})
            
            result = await self.conversation.insert_one({
                "session_id": session_id,
                "role": "summary",
                "content": summary_text,
                "is_summary": True,
                "timestamp": datetime.utcnow().isoformat(),
                "sources": None,
                "agent_name": "summary",
                "user_id": None,
            })
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error replacing messages with summary: {e}", exc_info=True)
            return None

    # Workflows
    
    async def get_workflows(self, creator_id: str):
        try:
            cursor = self.workflows.find({"creator_id": creator_id}).sort(
                "updated_timestamp", DESCENDING
            )
            workflows = []
            async for workflow in cursor:
                workflow.pop("_id", None)
                workflows.append(workflow)
            return workflows
        except PyMongoError as e:
            logger.error(f"Error retrieving workflows:{e}")
            return None

    async def get_workflow(self, workflow_id: str, creator_id: str):
        try:
            workflow = await self.workflows.find_one(
                {"id": workflow_id, "creator_id": creator_id}
            )
            return workflow
        except PyMongoError as e:
            logger.error(f"Error retrieving workflow {e}")
            return None

    async def delete_workflow(self, workflow_id: str, creator_id: str) -> bool:
        try:
            result = await self.workflows.delete_one(
                {"id": workflow_id, "creator_id": creator_id}
            )
            return result.deleted_count == 1
        except PyMongoError as e:
            logger.error(f"Error deleting workflow {e}")
            return False


    async def save_workflow(self, workflow: WorkflowBuilder) -> str | None:
        try:
            data = workflow.model_dump(mode="json")
            await self.workflows.insert_one(data)
            return workflow.id
        
        except PyMongoError as e:
            logger.error(f"Error saving workflow:{e}")
            return None

    async def update_workflow(self, workflow: WorkflowBuilder, creator_id: str) -> bool:
        try:
            data = workflow.model_dump(mode="json")
            data.pop("id", None)
            data.pop("creator_id", None)
            result = await self.workflows.update_one(
                {"id": workflow.id, "creator_id": creator_id},
                {"$set": data},
            )
            return result.matched_count == 1
        except PyMongoError as e:
            logger.error(f"Error updating workflow {e}")
            return False

        