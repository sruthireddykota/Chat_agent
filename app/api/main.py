from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.session_cleanup_scheduler import SessionCleanupScheduler
from app.utils.observability import congfigure_observability
from .auth import AuthenticationMiddleware
from .routers import admin, chat, documents, health, metrics, sessions, user, conversation, workflow

congfigure_observability()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.repositeries.mongodb_server import MongoStore
    from app.azure_clients.azure_client import get_client
    
    mongo_store = MongoStore()
    azure_client = None
    session_scheduler = None
    try:
        azure_client = await get_client()
        await mongo_store.connect()
        app.state.mongo_store = mongo_store
        app.state.azure_client = azure_client
        session_scheduler = SessionCleanupScheduler(mongo_store.logout_stale_users)
        session_scheduler.start()
        yield
    finally:
        if session_scheduler:
            await session_scheduler.stop()
        mongo_store.close()  # Ensure the MongoDB connection is closed when the app shuts down
        if azure_client:
            await azure_client.close()  # Ensure the Azure client is closed

app = FastAPI(
    title="FastAPI",
    version="1.0.0",
    lifespan=lifespan
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

app.add_middleware(AuthenticationMiddleware)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(user.router)
app.include_router(metrics.router)
app.include_router(admin.router)
app.include_router(conversation.router)
app.include_router(workflow.router)
