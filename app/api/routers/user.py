from __future__ import annotations

from fastapi import APIRouter, status, HTTPException
from pymongo.errors import PyMongoError

from app.models.mongo import LoginRequest
from app.repositeries.mongodb_server import MongoStore

mongo=MongoStore()
router=APIRouter(prefix="/api/v1",tags=["User"])

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: dict):
    try:
        result = mongo.create_user(user)
        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=result.get("message"))
        return result
    
    except HTTPException:
        raise

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"MongoDB Error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e))

@router.post("/users/status", status_code=status.HTTP_200_OK)
def update_user_status(user_id: str, logged_in: bool):
    try:
        update_status = mongo.update_user_status(user_id, logged_in)
        if not update_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found")
        return {"status": "updated"}
    
    except HTTPException:
        raise
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"MongoDB Error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e))

@router.get("/users/{email_id}",status_code=status.HTTP_200_OK)
def get_user(email_id: str):
    try:
        user = mongo.get_user_details(email_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No document found"
            )
        return user
        
    except PyMongoError  as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/user/login", status_code=status.HTTP_200_OK)
def login(request: LoginRequest):
    import bcrypt
    try:
        user_data = mongo.get_user_details(email_id=request.email_id)

        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user_data.get("logged_in"):
            return {"success": False, "message": "User already logged in"}

        password_bytes = request.password.encode("utf-8")
        hashed_password = user_data["password"]

        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode("utf-8")

        if not bcrypt.checkpw(password_bytes, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        mongo.update_user_status(user_data["user_id"], True)

        return {
            "success": True,
            "user_id": user_data["user_id"]
        }

    except HTTPException:
        raise

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {e}"
        )

@router.get("/user/logout/{user_id}",status_code=status.HTTP_200_OK)
def logout(user_id:str):
    try:
        mongo.update_user_status(user_id=user_id,logged_in=False)
        return {"success": True}
    
    except HTTPException:
        raise
    
    except PyMongoError as e:
        raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"MongoDB Error: {e}"
                ) 

