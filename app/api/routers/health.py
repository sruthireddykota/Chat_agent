from fastapi import APIRouter, status

router = APIRouter(prefix="/api/v1", tags=["Health"])

@router.get("/", status_code = status.HTTP_200_OK, summary = "Welcome message")
def read_root():
    return {"message": "Welcome to the Chat Application API!"}


@router.get("/health", status_code = status.HTTP_200_OK, summary = "Health check")
def health_check():
    return {"status": "healthy"}