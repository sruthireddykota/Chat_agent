from fastapi import APIRouter, status, HTTPException
from pymongo.errors import PyMongoError
from fastapi.encoders import jsonable_encoder
from pathlib import Path

from app.repositeries.mongodb_server import MongoStore
from app.models.agents import AgentRunRequest
from app.models.constants import AgentType
from app.agents.coder.coder_agent import CoderAgent
from app.agents.generic.generic_agent import GenericAgent
from app.agents.rag.rag_agent import RAGAgent
from app.agents.researcher.researcher_agent import ResearcherAgent
from app.utils.logger import get_logger
from app.config.settings import settings

mongo=MongoStore()
router=APIRouter(prefix="/api/v1",tags=["Chat"])
logger = get_logger()

AGENT_CLASSES = {
    AgentType.CODER: CoderAgent,
    AgentType.GENERIC: GenericAgent,
    AgentType.RAG: RAGAgent,
    AgentType.RESEARCHER: ResearcherAgent,
}


@router.post("/agent/run", status_code=status.HTTP_200_OK)
async def run_agent(request: AgentRunRequest):
    agent_class = AGENT_CLASSES.get(request.agent_name)
    if agent_class is None:
        raise HTTPException(status_code=400, detail="Unknown agent")

    try:
        agent = agent_class(session_id=request.session_id)
        response = await agent.invoke_agent(request.model_dump())
        if isinstance(response, dict):
            return response
        return {"response": response or ""}
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Agent request failed: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e


@router.get("/workspace/{session_id}", status_code=status.HTTP_200_OK)
def get_workspace(session_id: str):
    """Return text files generated in a Coder session workspace."""
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

def get_chat_history(session_id: str, limit: int = 10):

    try:
        data = mongo.get_chat_history(session_id, limit)

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
def save_message(message: dict):
    try:
        message_id = mongo.save_message(message)
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
def clear_chatmessages(session_id: str):
    try:
        deleted_messages=mongo.clear_chatmessages(session_id)
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
