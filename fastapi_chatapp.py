from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from Mongodb.mongodb_server import MongoStore
from pydantic import BaseModel

app = FastAPI()

mongo=MongoStore()

class SessionRequest(BaseModel):
    session_id: str
    user_id: str
    
@app.get("/")
def read_root():
    return {"message": "Welcome to the Chat Application API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/session/create")
def create_session(data: SessionRequest):
    return {"session_id": mongo.create_session(data.session_id, data.user_id)}

@app.get("/sessions/{user_id}")
def get_sessions(user_id: str, limit: int = 10):
    data = mongo.get_sessions(user_id, limit)
    return jsonable_encoder(data)

@app.get("/chat/{session_id}")
def get_chat_history(session_id: str, limit: int = 10):
    data = mongo.get_chat_history(session_id, limit)
    return jsonable_encoder(data)

@app.post("/message")
def save_message(message: dict):

    message["timestamp"] = datetime.utcnow().isoformat()

    return {"message_id": mongo.save_message(message)}

@app.delete("/chat/{session_id}")
def clear_chatmessages(session_id: str):
    return {"deleted_messages": mongo.clear_chatmessages(session_id)}

@app.delete("/session/delete")
def delete_session(session_id: str):
    return {"deleted": mongo.delete_session(session_id)}


@app.post("/documents/store")
def store_document(document: dict):
    return {"document_id": mongo.store_documents(document)}

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    return {"deleted": mongo.delete_document(document_id)}


@app.get("/documents/get")
def get_documents():
    return mongo.get_documents()

@app.post("/users")
def create_user(user: dict):
    return mongo.create_user(user)

@app.post("/users/status")
def update_user_status(user_id: str, logged_in: bool):
    mongo.update_user_status(user_id, logged_in)
    return {"status": "updated"}


@app.get("/users/{email_id}")
def get_user(email_id: str):
    return mongo.get_user_details(email_id)