from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from datetime import datetime
from app.utils.logger import get_logger
from app.config.settings import settings
from app.models.mongo import (MongoStoreMessage,MongoDocumentData, MongoUser, UserDetails)

logger=get_logger()

class MongoStore:
    def __init__(self):
        self._MONGO_URI =settings.MONGODB_URI
        self._MONGODB_DB =settings.MONGODB_DB
        self.KM_DB=settings.MONGODB_KM_DB
        self.USERS_DB=settings.MONGODB_USER_DB
        
        try:
            self.client = MongoClient(self._MONGO_URI, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            logger.info("Connected to MongoDB")
        except ConnectionFailure as e:
            logger.error("MongoDB connection failed: %s", e)
            raise
        
        self.db = self.client[self._MONGODB_DB]
        self.km_db=self.client[self.KM_DB]
        self.users_db=self.client[self.USERS_DB]
        
        self.rag_logs = self.db["rag_logs"]
        self.sessions = self.db["sessions"]
        self.messages = self.db["chatmessages"]
        self.documents=self.km_db["documents"]
        self.users=self.users_db["users"]
        self._create_index()
    
    
    def create_title(self, content):
        from app.azure_clients.title_azure_client import get_client
        logger.info("Generating title for content preview: %s", content.strip()[:50])
        client=get_client()
        content_preview=content.strip()[:200]
        response = client.chat.completions.create(
            # Title generation uses its own Azure OpenAI deployment. Agent
            # requests use AZURE_OPENAI_DEPLOYMENT through Foundry instead.
            model=settings.AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "create a title in 2-3 words from the content"},
                {"role": "user", "content": content_preview}
            ],
            max_tokens=10
        )
        title=response.choices[0].message.content
        title = title.strip().strip('"').strip("'")
        logger.info("Generated title: %s", title)
        return title
        
    def _create_index(self):        
        self.sessions.create_index([("session_id", 1)], unique=True)
        self.sessions.create_index([("user_id", 1), ("updated_at", DESCENDING)])
        self.sessions.create_index([("user_id", 1), ("message_count", DESCENDING)])
        self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        self.rag_logs.create_index([("session_id", 1), ("timestamp", 1)])
        
    def create_session(self, session_id: str, user_id: str):
        try:
            result = self.sessions.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "title": "New Chat",
                "message_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
            return str(result.inserted_id)
        except Exception as e:
            return None

    def get_sessions(self, user_id: str, limit: int = 10):
        try:
            sessions = self.sessions.find({'user_id': user_id}).sort("updated_at", DESCENDING).limit(limit)
            result = []
            for session in sessions:
                session["_id"] = str(session["_id"])
                result.append(session)

            return result
        except Exception as e:
            return None
    
    def delete_session(self, session_id):
        try:
            result = self.messages.delete_many({"session_id": session_id})
            if result:
                output = self.sessions.delete_one({"session_id": session_id})
            
            logger.info(f"Deleted session_id: {session_id}, messages_deleted: {result.deleted_count}, session_deleted: {output.deleted_count if result else 0}")
            return output.deleted_count > 0
        except Exception as e:
            return None
    
    def get_chat_history(self, session_id: str, limit: int = 10):
        try:
            messages = (
                self.messages
                .find({'session_id': session_id})
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            result = []
            for message in messages:
                message["_id"] = str(message["_id"])
                result.append(message)
            result.reverse()  
            return result
        except Exception as e:
            return None

    def save_message(self, message: MongoStoreMessage) -> str:
        try:
            timestamp = message.get("timestamp") or datetime.utcnow().isoformat()

            result = self.messages.insert_one({
                "session_id": message["session_id"],
                "role": message["role"],
                "content": message["content"],
                "timestamp": timestamp,
                "sources": message["sources"],
                "agent_name": message["agent_name"],
                "user_id": message["user_id"]
            })
            
            self.sessions.update_one(
                {"session_id": message.get("session_id")},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": datetime.utcnow().isoformat()}
                })
            
            
            if message.get("role") == "user":
                session_output = list(self.sessions.find({'session_id': message.get("session_id")}))
                count = session_output[0].get("message_count")
                if count == 1:
                    content = message.get("content")
                    
                    if content and content.strip():
                        try:
                            title = self.create_title(content)  
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
                        
                    self.sessions.update_one(
                        {"session_id": message.get("session_id")},
                        {
                            "$set": {"title": title, "updated_at": datetime.utcnow().isoformat()}
                        }
                    )
            logger.info(f"Saved message for session_id: {message.get('session_id')}, role: {message.get('role')}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            return None

    def clear_chatmessages(self, session_id):
        try:
            result = self.messages.delete_many({"session_id": session_id})
            
            self.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {"message_count": 0, "updated_at": datetime.utcnow().isoformat()}
                }
            )
            logger.info(f"Cleared chat messages for session_id: {session_id}, deleted_count: {result.deleted_count}")
            return result.deleted_count
        except Exception as e:
            return None
    

    def store_documents(self, document_data: MongoDocumentData):
        try:
            self.documents.insert_one({
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
        
    def delete_document(self,document_id):
        try:
            response=self.documents.delete_one({
                "document_id":document_id
            })
            return response.deleted_count > 0 
        except Exception as e:
            return False
    
    def get_documents(self):
        try:
            response=self.documents.find().sort("timestamp",1)
            
            result = []
            for message in response:
                message["_id"] = str(message["_id"])
                result.append(message)
            return result
        except Exception as e:
            return None
    
    def create_user(self,user_data : MongoUser):
        try:
            data={
                "username":user_data.get("username"),
                "user_id":user_data.get("user_id"),
                "password":user_data.get("password"),
                "email_id":user_data.get("email_id"),
                "created_at":datetime.utcnow().isoformat(),
                "logged_in":user_data.get("logged_in"),
                "last_logged_in":user_data.get("last_logged_in")
            }
            response=self.users.find({
                "username":user_data.get("username")
            })
            if len(list(response))>0:
                return {
                    'status':"Fail",
                    'message':'Username already Exists'
                }
            
            else:
                response=self.users.find({
                "email_id":user_data.get("email_id")
                })
                if len(list(response))>0:
                    return {
                    'status':"Fail",
                    'message':'Email_id already Exists'
                }
                else:
                    self.users.insert_one(data)
                    return {
                    'status':"success",
                    'message':'Sign UP Successful!'
                }
                
        except Exception as e:
            return {
                    'status':"Fail",
                    'message': f'Error:{e}'
                }
    
    def update_user_status(self, user_id, logged_in):
        try:
            if logged_in:
                result = self.users.update_one({"user_id": user_id}, {"$set": {"logged_in": logged_in, "last_logged_in": datetime.utcnow().isoformat()}})
            else:
                result = self.users.update_one({"user_id": user_id}, {"$set": {"logged_in": logged_in}})
            if result.matched_count == 0:
                return None
            return True
        except Exception as e:
            logger.error("Error updating user status: %s", e)
            return None
    
    def get_user_details(self,email_id)-> UserDetails:
        try:
            response=self.users.find({
                "email_id":email_id
            })
            result=list(response)[0]
            user_details={
                "username":result.get("username"),
                "password":result.get("password"),
                "user_id":result.get("user_id"),
                "email_id":result.get("email_id"),
                "logged_in":result.get("logged_in")
            }
            return user_details
        except Exception as e:
            return None
    
    def get_login_details(self,email_id):
        try:

            response=self.users.find({
                "email_id":email_id
            })
            result=list(response)

            user=result[0]
            logged_in = user.get("logged_in")
            last_logged_in = user.get("last_logged_in")

            if logged_in and last_logged_in:
                last_login_time = datetime.fromisoformat(last_logged_in)
                time_duration=datetime.utcnow()-last_login_time
                if time_duration.total_seconds() > 3600:
                    self.users.update_one(
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

    def save_rag_log(self, session_id, query, context, answer):
        try:
            self.rag_logs.insert_one({
                "session_id": session_id,
                "query": query,
                "context": context,    
                "answer": answer,         
                "timestamp": datetime.utcnow().isoformat()
            })
            logger.info(f"Saved RAG log for session_id: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save RAG log: {e}")
    
    def get_average_metrics(self):
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
            result = list(collection.aggregate(pipeline))
            
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
