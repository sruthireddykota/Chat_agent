from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from datetime import datetime

class MongoStore:
    def __init__(self):
        self._MONGO_URI = "mongodb://admin:strongpassword123@localhost:27017/?authSource=admin"
        self._MONGODB_DB = "chatbot_db"
        self.KM_DB="documents_db"
        self.USERS_DB="users_db"
        try:
            self.client = MongoClient(self._MONGO_URI, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            print("Connected to MongoDB")
        except ConnectionFailure as e:
            print("MongoDB connection failed:", e)
            raise
        
        self.db = self.client[self._MONGODB_DB]
        self.km_db=self.client[self.KM_DB]
        self.users_db=self.client[self.USERS_DB]
        
        self.sessions = self.db["sessions"]
        self.messages = self.db["chatmessages"]
        self.documents=self.km_db["documents"]
        self.users=self.users_db["users"]
        self._create_index()
    
    
    def create_title(self, content):
        from azure_clients.title_azure_client import get_client
        
        client=get_client()
        content_preview=content.strip()[:200]
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "create a title in 2-3 words from the content"},
                {"role": "user", "content": content_preview}
            ],
            max_tokens=10
        )
        title=response.choices[0].message.content
        
        title = title.strip().strip('"').strip("'")
        return title
        
    def _create_index(self):        
        self.sessions.create_index([("session_id", 1)], unique=True)
        self.sessions.create_index([("user_id", 1), ("updated_at", DESCENDING)])
        self.sessions.create_index([("user_id", 1), ("message_count", DESCENDING)])
        self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        
    def create_session(self, session_id: str, user_id: str):
        result = self.sessions.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "title": "New Chat",
            "message_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        return result.inserted_id
    
    def get_sessions(self, user_id: str, limit: int = 10):
        sessions = self.sessions.find({'user_id': user_id}).sort("updated_at", DESCENDING).limit(limit)
        return list(sessions)
    
    def get_chat_history(self, session_id: str, limit: int = 10):
        messages = self.messages.find({'session_id': session_id}).sort("timestamp", 1).limit(limit)
        return list(messages)
    
    def save_message(self, message):
        result = self.messages.insert_one({
            "session_id": message.get("session_id"),
            "role": message.get("role"),
            "content": message.get("content"),
            "timestamp": message.get("timestamp"),
            "sources": message.get("sources"),
            "agent_name": message.get("agent_name"),
            "user_id": message.get("user_id")
        })
        
        self.sessions.update_one(
            {"session_id": message.get("session_id")},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            })
        
        session_output = list(self.sessions.find({'session_id': message.get("session_id")}))
        count = session_output[0].get("message_count")
        
        if count == 1 and message.get("role") == "user":
            content = message.get("content")
            
            if content and content.strip():
                try:
                    title = self.create_title(content)  
                    if not isinstance(title, str):
                        title = str(title) if title else "New Chat"
                    title = title.strip()[:50]
                except Exception as e:
                    print(f"Error generating title: {e}")
                    title = "New Chat"
            else:
                title = "New Chat"
                
            self.sessions.update_one(
                {"session_id": message.get("session_id")},
                {
                    "$set": {"title": title, "updated_at": datetime.utcnow().isoformat()}
                }
            )
            
        return result.inserted_id
    
    def clear_chatmessages(self, session_id):
        result = self.messages.delete_many({"session_id": session_id})
        
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"message_count": 0, "updated_at": datetime.utcnow().isoformat()}
            }
        )
        return result.deleted_count
    
    def delete_session(self, session_id):
        result = self.messages.delete_many({"session_id": session_id})
        if result:
            output = self.sessions.delete_one({"session_id": session_id})
        return output.deleted_count > 0
    
    
    def store_documents(self,document_data):
        response= self.documents.insert_one({
            "document_name":document_data.get("document_name"),
            "document_id":document_data.get("document_id"),
            "document_type":document_data.get("document_type"),
            "timestamp":document_data.get("timestamp"),
            "chunk_count":document_data.get("chunk_count"),
            "uploaded_by":document_data.get("uploaded_by"),
            "tags":document_data.get("tags")
        })
        return response
    
    def delete_document(self,document_id):
        response=self.documents.delete_one({
            "document_id":document_id
        })
        return response.deleted_count > 0 
    
    def get_documents(self):
        response=self.documents.find().sort("timestamp",1)
        
        return list(response)
    
    def create_user(self,user_data):
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
    def update_user_status(self,user_id,logged_in):
        
        if logged_in:
            
            self.users.update_one({
                "user_id":user_id},{
                    "$set":{"logged_in":logged_in,"last_logged_in":datetime.utcnow().isoformat()}
                }
            )
        else:
            self.users.update_one({
                "user_id":user_id},{
                    "$set":{"logged_in":logged_in}
                }
            )
    
    def get_user_details(self,email_id):
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
    
    
        
            
        
    
    