from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

class MongoStore:
    def __init__(self):
        user=os.getenv("MONGO_USER")
        password=os.getenv("MONGO_PASSWORD")
        host=os.getenv("MONGO_HOST")
        port=os.getenv("MONGO_PORT")
        
        self._MONGO_URI = f'mongodb://{user}:{password}@{host}:{port}/?authSource=admin'
        self._MONGODB_DB = os.getenv("MONGODB_MESSAGEDB_NAME")
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
   
    
    
    
    
    

    
    