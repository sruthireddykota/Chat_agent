from __future__ import annotations

from fastapi import APIRouter, status, HTTPException, Request
from pymongo.errors import PyMongoError

from app.models.mongo import LoginRequest
from app.api.auth import create_access_token, current_user, require_user_id

router=APIRouter(prefix="/api/v1",tags=["User"])

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: dict, req: Request):
    mongo = req.app.state.mongo_store
    try:
        result = await mongo.create_user(user)
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
async def update_user_status(user_id: str, logged_in: bool, req: Request):
    require_user_id(req, user_id)
    mongo = req.app.state.mongo_store
    try:
        update_status = await mongo.update_user_status(user_id, logged_in)
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
async def get_user(email_id: str, req: Request):
    current_user(req)
    mongo = req.app.state.mongo_store
    try:
        user = await mongo.get_user_details(email_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No document found"
            )
        user.pop("password", None)
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
async def login(request: LoginRequest, req: Request):
    import bcrypt
    mongo = req.app.state.mongo_store
    try:
        user_data = await mongo.get_user_details(email_id=request.email_id)

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

        await mongo.update_user_status(user_data["user_id"], True)

        role = user_data.get("role", "user")
        access_token = create_access_token(
            user_id=user_data["user_id"],
            email_id=request.email_id,
            role=role,
        )

        return {
            "success": True,
            "user_id": user_data["user_id"],
            "role": role,
            "access_token": access_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {e}"
        )

@router.get("/user/logout/{user_id}",status_code=status.HTTP_200_OK)
async def logout(user_id:str, req: Request):
    require_user_id(req, user_id)
    mongo = req.app.state.mongo_store
    try:
        await mongo.update_user_status(user_id=user_id,logged_in=False)
        return {"success": True}
    
    except HTTPException:
        raise
    
    except PyMongoError as e:
        raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"MongoDB Error: {e}"
                ) 
