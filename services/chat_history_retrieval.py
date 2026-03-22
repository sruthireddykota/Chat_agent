from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.settings import settings

class MongoStore:
    def __init__(self):
        
        self._MONGO_URI = settings.MONGODB_URI
        self._MONGODB_DB = settings.MONGODB_DB
        try:
            self.client = MongoClient(self._MONGO_URI, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            print("Connected to MongoDB")
        except ConnectionFailure as e:
            print("MongoDB connection failed:", e)
            raise
        
        self.db = self.client[self._MONGODB_DB]
        self.messages = self.db["chatmessages"]
    
    def get_chat_history(self, session_id: str, limit: int = 10):
        messages = self.messages.find({'session_id': session_id}).sort("timestamp", 1).limit(limit)
        chat_history=""
        for chat_message in list(messages):
            role=chat_message.get("role")
            content=chat_message.get("content")
            response= f"Role:{role} \n Content: {content} \n"
            chat_history+=response
        return chat_history 
   
    
    
    
    
    

    
    