from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import admin, chat, documents, health, metrics, sessions, user

app = FastAPI(
    title="FastAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost/",
        "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(user.router)
app.include_router(metrics.router)
app.include_router(admin.router)
