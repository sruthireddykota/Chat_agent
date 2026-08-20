from fastapi import APIRouter, Request, HTTPException, status

from app.api.dependencies import SummarizeRequest, ReplaceSummaryRequest
from app.utils.logger import get_logger
from app.api.auth import require_session_owner

router=APIRouter(prefix="/api/v1",tags=["Conversation"])
logger = get_logger()

@router.get("/sessions/{session_id}/conversation-count",status_code=status.HTTP_200_OK)
async def conversation_count(session_id: str,req: Request):
    await require_session_owner(req, session_id)
    try:
        mongodb_storage = req.app.state.mongo_store
        count = await mongodb_storage.get_conversation_count(session_id)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Failed to fetch conversation count: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e

@router.get("/sessions/{session_id}/conversation-messages",status_code=status.HTTP_200_OK)
async def conversation_messages(req: Request, session_id: str, limit: int = 10):
    await require_session_owner(req, session_id)
    try:
        mongodb_storage = req.app.state.mongo_store
        messages = await mongodb_storage.get_conversation_messages(session_id, limit)
        if messages is None:
            raise HTTPException(500, "Failed to fetch conversation messages")
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Failed to fetch conversation messages: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e


@router.post("/sessions/{session_id}/summarize",status_code=status.HTTP_200_OK)
async def summarize_conversation(session_id: str, payload: SummarizeRequest, req: Request):
    await require_session_owner(req, session_id)
    azure_client = req.app.state.azure_client
    try:
        from app.services.summarization_service import SummarizationService

        summarization_service = SummarizationService(azure_client)
        summary = await summarization_service.summarize_conversation(payload.messages)
        return {"summary": summary}
    
    except HTTPException:
        raise
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Failed to summarize conversation: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e


@router.post("/sessions/{session_id}/replace-with-summary",status_code=status.HTTP_200_OK)
async def replace_with_summary(session_id: str, payload: ReplaceSummaryRequest,req: Request):
    await require_session_owner(req, session_id)
    try:
        mongodb_storage = req.app.state.mongo_store
        summary_id = await mongodb_storage.replace_with_summary(
            session_id, payload.summary
        )
        if not summary_id:
            raise HTTPException(500, "Failed to replace messages with summary")
        return {"status": "ok", "summary_id": summary_id}
    except HTTPException:
        raise
    except Exception as e:
        cause = e.__cause__ or e
        logger.error("Failed to replace messages with summary: %s", cause, exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(cause).__name__}: {cause}") from e
