import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, status, HTTPException, Request
from fastapi.responses import StreamingResponse
from pymongo.errors import PyMongoError
from fastapi.encoders import jsonable_encoder

from app.config.settings import settings
from app.models.agents import AgentRequest
from app.models.constants import AgentType
from app.agents.coder.coder_agent import CoderAgent
from app.agents.generic.generic_agent import GenericAgent
from app.agents.rag.rag_agent import RAGAgent
from app.agents.researcher.researcher_agent import ResearcherAgent
from app.agents.base.redis_manager import RedisManager

from app.utils.logger import get_logger
from app.api.auth import current_user, require_session_owner

router=APIRouter(prefix="/api/v1",tags=["Chat"])
logger = get_logger()

AGENT_CLASSES = {
    AgentType.CODER.value: CoderAgent,
    AgentType.GENERIC.value: GenericAgent,
    AgentType.RAG.value: RAGAgent,
    AgentType.RESEARCHER.value: ResearcherAgent,
}

@router.post("/agent/run", status_code=status.HTTP_200_OK)
async def run_agent(request: AgentRequest, req: Request):
    user = current_user(req)
    if user.get("sub") != request.user_id:
        raise HTTPException(status_code=403, detail="User access denied")
    await require_session_owner(req, request.session_id)
    agent_class = AGENT_CLASSES.get(request.agent_name.value)
    if agent_class is None:
        raise HTTPException(status_code=400, detail="Unknown agent")

    try:
        agent = agent_class(session_id=request.session_id)
        agent_request = request.model_dump()
        agent_request["authorization"] = req.headers.get("Authorization")
        response = await agent.invoke_agent(agent_request)
        if isinstance(response, dict):
            return response
        return {"response": response or ""}
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Agent request failed: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e


@router.post("/agent/stream")
async def stream_agent(request: AgentRequest,req: Request):
    """Run an agent and forward its Redis-published chunks as SSE events."""
    try:
        user = current_user(req)
        if user.get("sub") != request.user_id:
            raise HTTPException(status_code=403, detail="User access denied")
        await require_session_owner(req, request.session_id)
        agent_class = AGENT_CLASSES.get(request.agent_name.value)
        if agent_class is None:
            raise HTTPException(status_code=400, detail="Unknown agent")

        redis_manager = RedisManager()
        channel = f"redis_{request.session_id}"

        azure_client = req.app.state.azure_client
        mongo_store = req.app.state.mongo_store

        async def event_stream():
            task = asyncio.create_task(
                agent_class(
                    session_id=request.session_id,
                    mongodb_storage=mongo_store,
                    azure_client=azure_client,
                ).invoke_agent(
                    {
                        **request.model_dump(),
                        "authorization": req.headers.get("Authorization"),
                    }
                )
            )
            try:
                async for envelope in redis_manager.subscribe(channel):
                    if envelope.get("type") in ("completed", "error"):
                        try:
                            await task
                        except Exception as exc:
                            logger.error("Streaming agent request failed: %s", exc, exc_info=True)
                    yield f"data: {json.dumps(envelope)}\n\n"
                    if envelope.get("type") in ("completed", "error"):
                        break
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Streaming agent request failed: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e
@router.get("/workspace/{session_id}", status_code=status.HTTP_200_OK)
async def get_workspace(session_id: str, req: Request):
    """Return text files generated in a Coder session workspace."""

    await require_session_owner(req, session_id)
    workspace = (Path(settings.CODER_BASE_PATH) / session_id).resolve()
    base = Path(settings.CODER_BASE_PATH).resolve()
    if base not in workspace.parents:
        raise HTTPException(status_code=400, detail="Invalid session id")

    if not workspace.exists():
        return {"files": {}}

    files = {}
    for path in sorted(workspace.rglob("*")):
        if not path.is_file() or any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in path.parts):
            continue
        relative = path.relative_to(workspace).as_posix()
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files[relative] = {"content": content[:500_000]}

    return {"files": files}

@router.get("/chat/{session_id}", status_code=status.HTTP_200_OK)
async def get_chat_history(req: Request,session_id: str, limit: int = 10):
    await require_session_owner(req, session_id)
    mongo = req.app.state.mongo_store
    try:
        data = await mongo.get_chat_history(session_id, limit)

        if data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract the data"
            )

        return jsonable_encoder(data)

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/message",status_code=status.HTTP_200_OK)
async def save_message(message: dict, req: Request):
    user = current_user(req)
    if user.get("sub") != message.get("user_id"):
        raise HTTPException(status_code=403, detail="User access denied")
    await require_session_owner(req, message.get("session_id"))
    mongo = req.app.state.mongo_store
    try:
        message_id = await mongo.save_message(message)
        if message_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message Id is missing"
            )
        return {"message_id":message_id}
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/chat/{session_id}",status_code=status.HTTP_200_OK)
async def clear_chatmessages(session_id: str,req: Request):
    await require_session_owner(req, session_id)
    mongo = req.app.state.mongo_store
    try:
        deleted_messages = await mongo.clear_chatmessages(session_id)
        if deleted_messages is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session ID not found"
            )
        return {"deleted_messages": deleted_messages}
    
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
