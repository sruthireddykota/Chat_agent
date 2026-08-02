from fastapi import APIRouter, status, HTTPException, UploadFile, File, Form
from pymongo.errors import PyMongoError
from app.config.settings import settings
from app.services.chunking import generate_chunks
from app.services.embeddings import generate_embeddings
from app.services.qdrant_store import Qdrantservice
import httpx
import json
import uuid
import os

from app.repositeries.mongodb_server import MongoStore, MongoDocumentData



mongo=MongoStore()
router=APIRouter(prefix="/api/v1",tags=["Documents"])


@router.post("/documents/parse", status_code=status.HTTP_200_OK)
async def parse_document(
    file: UploadFile = File(...),
    options: str = Form("{}"),
):
    """Proxy document parsing to the Docling service used by the original flow."""
    try:
        opts = json.loads(options)
        content = await file.read()
        data = {
            "to_formats": [opts.get("format", "md")],
            "do_ocr": str(opts.get("ocr", False)).lower(),
            "do_table_structure": str(opts.get("table", True)).lower(),
            "do_picture_description": str(opts.get("picture", True)).lower(),
            "do_code_enrichment": str(opts.get("code", False)).lower(),
            "do_formula_enrichment": str(opts.get("formula", False)).lower(),
            "images_scale": str(opts.get("image_scale", 2)),
            "table_mode": str(opts.get("table_mode", "fast")).lower(),
            "image_export_mode": "referenced",
            "pipeline_options": json.dumps({"enable_remote_services": True}),
        }
        if opts.get("picture", True):
            data["picture_description_api"] = json.dumps({
                "url": os.getenv("VISION_END_POINT"),
                "concurrency": 1,
                "headers": {
                    "api-key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "Content-Type": "application/json",
                },
                "params": {"model": os.getenv("VISION_DEPLOYMENT_NAME")},
                "timeout": 600,
                "prompt": "Describe this image in a few sentences",
            })
        files = {"files": (file.filename, content, file.content_type or "application/octet-stream")}
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                "http://docling-serve:5001/v1/convert/file",
                data=data,
                files=files,
            )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        result = response.json()
        document = result.get("document") or {}
        return {
            "document_id": str(uuid.uuid4()),
            "filename": file.filename,
            "status": result.get("status"),
            "processing_time": result.get("processing_time", 0),
            "errors": result.get("errors", []),
            "document": document,
            "content": document.get(f"{opts.get('format', 'md')}_content")
                or document.get("md_content")
                or document.get("text_content")
                or "",
        }
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


@router.post("/documents/parse-url", status_code=status.HTTP_200_OK)
async def parse_document_url(payload: dict):
    try:
        opts = payload.get("options", {})
        urls = [url.strip() for url in payload.get("urls", []) if url.strip()]
        if not urls:
            raise HTTPException(status_code=400, detail="At least one URL is required")
        options = {
            "to_formats": [opts.get("format", "md")],
            "do_ocr": opts.get("ocr", False),
            "do_table_structure": opts.get("table", True),
            "do_picture_description": opts.get("picture", True),
            "do_code_enrichment": opts.get("code", False),
            "do_formula_enrichment": opts.get("formula", False),
            "images_scale": opts.get("image_scale", 2),
            "table_mode": opts.get("table_mode", "fast"),
            "image_export_mode": "referenced",
            "pipeline_options": {"enable_remote_services": True},
        }
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                "http://docling-serve:5001/v1/convert/source",
                json={"options": options, "sources": [{"kind": "http", "url": url} for url in urls], "target": {"kind": "inbody"}},
            )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        result = response.json()
        document = result.get("document") or {}
        content = document.get(f"{opts.get('format', 'md')}_content") or document.get("md_content") or document.get("text_content") or ""
        return {"document_id": str(uuid.uuid4()), "filename": document.get("filename", urls[0]), "status": result.get("status"), "processing_time": result.get("processing_time", 0), "errors": result.get("errors", []), "document": document, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
def store_document(document: MongoDocumentData):
    try:
        success = mongo.store_documents(document)
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
def delete_document(document_id: str):
    try:
        deleted = mongo.delete_document(document_id)
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

def get_documents():
    try:
        result = mongo.get_documents()

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
