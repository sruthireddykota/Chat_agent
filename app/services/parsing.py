from fastapi import HTTPException, UploadFile, File, Form
from app.config.settings import settings

import httpx
import json
import uuid
import os

class DoclingService:
    def __init__(self):
        self.docling_file_url = settings.DOCLING_FILE_URL
        self.docling_document_url = settings.DOCLING_DOCUMENT_URL

    async def parse_document(
        self,
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
                    self.docling_file_url,
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

    async def parse_document_url(self, payload: dict):
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
                    self.docling_document_url,
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