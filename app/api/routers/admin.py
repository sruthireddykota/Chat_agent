from fastapi import APIRouter, status,HTTPException,Request
from pymongo.errors import PyMongoError
from app.api.auth import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("",status_code=status.HTTP_200_OK)
async def login_details(email_id: str, req: Request):
    require_role(req, "admin")
    try:
        mongo = req.app.state.mongo_store
        user_login = await mongo.get_login_details(email_id=email_id)
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
