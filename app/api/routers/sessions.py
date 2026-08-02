from fastapi import APIRouter, status, HTTPException
from fastapi.encoders import jsonable_encoder
from pymongo.errors import PyMongoError

from app.repositeries.mongodb_server import MongoStore
from app.api.dependencies import SessionRequest

mongo = MongoStore()

router = APIRouter(prefix="/api/v1", tags=["Sessions"])


@router.post("/session/create", status_code=status.HTTP_201_CREATED)
def create_session(data: SessionRequest):
    try:
        session_id = mongo.create_session(data.session_id, data.user_id)

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
def get_sessions(user_id: str, limit: int = 10):
    try:
        sessions = mongo.get_sessions(user_id, limit)

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
def delete_session(session_id: str):
    try:
        deleted = mongo.delete_session(session_id)

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