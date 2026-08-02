from fastapi import APIRouter, status,HTTPException
from pymongo.errors import PyMongoError
from app.repositeries.mongodb_server import MongoStore


mongo=MongoStore()
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("",status_code=status.HTTP_200_OK)
def login_details(email_id: str,):
    try:

        user_login = mongo.get_login_details(email_id=email_id)
        if user_login is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user details"
            )

        return user_login

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