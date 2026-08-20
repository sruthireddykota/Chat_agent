from fastapi import APIRouter, status, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pymongo.errors import PyMongoError

from app.api.dependencies import SessionRequest
from app.api.auth import require_user_id, require_session_owner

router = APIRouter(prefix="/api/v1", tags=["Sessions"])


@router.post("/session/create", status_code=status.HTTP_201_CREATED)
async def create_session(data: SessionRequest, req: Request):
    require_user_id(req, data.user_id)
    mongo = req.app.state.mongo_store
    try:
        session_id = await mongo.create_session(data.session_id, data.user_id)

        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session."
            )

        return {"session_id": session_id}

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
    
@router.get("/sessions/{user_id}", status_code=status.HTTP_200_OK)
async def get_sessions(req: Request, user_id: str, limit: int = 10):
    require_user_id(req, user_id)
    mongo = req.app.state.mongo_store
    try:
        sessions = await mongo.get_sessions(user_id, limit)

        if sessions is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sessions found."
            )

        return jsonable_encoder(sessions)

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


@router.delete("/session/delete", status_code=status.HTTP_200_OK)
async def delete_session(session_id: str, req: Request):
    await require_session_owner(req, session_id)
    mongo = req.app.state.mongo_store
    try:
        deleted = await mongo.delete_session(session_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found."
            )

        return {
            "deleted": True,
            "message": "Session deleted successfully."
        }

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
