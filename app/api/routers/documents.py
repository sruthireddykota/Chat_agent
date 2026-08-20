from fastapi import APIRouter, status, HTTPException, Request, UploadFile, File, Form
from pymongo.errors import PyMongoError

from app.repositeries.mongodb_server import MongoDocumentData
from app.services.chunking import generate_chunks
from app.services.embeddings import generate_embeddings
from app.services.qdrant_store import Qdrantservice
from app.api.auth import current_user

router=APIRouter(prefix="/api/v1",tags=["Documents"])

@router.post("/documents/parse", status_code=status.HTTP_200_OK)
async def parse_document(
    req: Request,
    file: UploadFile = File(...),
    options: str = Form("{}"),
):
    
    """Proxy document parsing to the Docling service used by the original flow."""
    current_user(req)
    
    try:
        from app.services.parsing import DoclingService
        docling_service = DoclingService()
        result = await docling_service.parse_document(file, options)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/documents/parse-url", status_code=status.HTTP_200_OK)
async def parse_document_url(payload: dict, req: Request):
    current_user(req)
    try:
        from app.services.parsing import DoclingService
        docling_service = DoclingService()
        result = await docling_service.parse_document_url(payload)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/documents/chunks", status_code=status.HTTP_200_OK)
def create_document_chunks(payload: dict):
    content = payload.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Document content is required")
    return {"chunks": generate_chunks(content)}

@router.post("/documents/embeddings", status_code=status.HTTP_200_OK)
def create_document_embeddings(payload: dict):
    chunks = payload.get("chunks", [])
    if not chunks:
        raise HTTPException(status_code=400, detail="Chunks are required")
    return {"embeddings": generate_embeddings(chunks)}


@router.post("/documents/store-embeddings", status_code=status.HTTP_200_OK)
def store_document_embeddings(payload: dict):
    chunks = payload.get("chunks", [])
    embeddings = payload.get("embeddings", [])
    if not chunks or not embeddings:
        raise HTTPException(status_code=400, detail="Chunks and embeddings are required")
    service = Qdrantservice()
    service.verify_collection("Documents")
    success, message = service.store_embeddings(
        "Documents",
        embeddings,
        {
            "chunks": chunks,
            "document_name": payload.get("document_name"),
            "document_id": payload.get("document_id"),
        },
    )
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"message": message}
    
@router.post("/documents/store", status_code=status.HTTP_200_OK)
async def store_document(document: MongoDocumentData,req: Request):
    current_user(req)
    mongo = req.app.state.mongo_store
    try:
        success = await mongo.store_documents(document)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No document found")
        return {"document_id": document.document_id}
    
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


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: str, req: Request):
    current_user(req)
    mongo = req.app.state.mongo_store
    try:
        deleted = await mongo.delete_document(document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No document id found")
        return {"deleted": deleted}
    
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


@router.get("/documents/get",status_code=status.HTTP_200_OK)
async def get_documents(req: Request):
    current_user(req)
    mongo = req.app.state.mongo_store
    try:
        result = await mongo.get_documents()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No document found"
            )

        return result

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
