import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.backend.agent_service import DocumentAgent
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

os.makedirs(settings.upload_dir, exist_ok=True)
agent = DocumentAgent()


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {extension}")

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read uploaded file: {str(exc)}") from exc

    if not content:
        raise HTTPException(status_code=400, detail="The selected file is empty")

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File exceeds the maximum size of {settings.max_upload_size_mb}MB")

    destination_path = Path(settings.upload_dir) / file.filename
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with open(destination_path, "wb") as target_file:
        target_file.write(content)

    try:
        chunks = agent.ingest_file(str(destination_path), file.filename)
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text was found in this document. For scanned PDFs, "
                    "install Tesseract OCR and upload the file again."
                ),
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(exc)}") from exc

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "chunks": len(chunks),
        "message": "File uploaded and indexed successfully."
    }


@app.post("/ask")
async def ask_question(payload: dict):
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = agent.answer_question(question)
    return result


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
