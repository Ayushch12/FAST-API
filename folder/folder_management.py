
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4

# Models from models.py
from models import FolderCreate, FolderCreateResponse, DocumentInFolder, DocumentCreateResponse, FolderUpdate, FolderUpdateResponse

router = APIRouter()

# In-memory databases
folders_db: Dict[str, Dict] = {}
documents_db: Dict[str, Dict] = {}


# Folder creation endpoint
@router.post("/api/folders/", response_model=FolderCreateResponse)
def create_folder(folder_data: FolderCreate):
    folder_id = str(uuid4())
    new_folder = folder_data.dict()
    new_folder["documents"] = []  # Initialize an empty list for documents
    folders_db[folder_id] = new_folder
    return {
        "success": True,
        "message": "Dossier créé avec succès.",
        "folderId": folder_id
    }


# Document upload and add to folder endpoint
@router.post("/api/folders/{folder_id}/documents/", response_model=DocumentCreateResponse)
def upload_document_to_folder(folder_id: str, file: UploadFile = File(...)):
    if folder_id not in folders_db:
        raise HTTPException(status_code=404, detail="Folder not found")
    document_id = str(uuid4())
    documents_db[document_id] = {
        "name": file.filename,
        "content_type": file.content_type,
    }
    folders_db[folder_id]["documents"].append(document_id)
    return DocumentCreateResponse(documentId=document_id, name=file.filename, content_type=file.content_type)

# Retrieve documents in a folder endpoint
@router.get("/api/folders/{folder_id}/documents/")
def get_documents_from_folder(folder_id: str):
    if folder_id not in folders_db:
        raise HTTPException(status_code=404, detail="Folder not found")
    document_list = [
        {
            "documentId": doc_id,
            **documents_db[doc_id],
        }
        for doc_id in folders_db[folder_id]["documents"]
    ]
    return {"documents": document_list}

# Update folder information endpoint
@router.put("/api/folders/{folder_id}/", response_model=FolderUpdateResponse)
def update_folder(folder_id: str, folder_data: FolderUpdate):
    if folder_id not in folders_db:
        raise HTTPException(status_code=404, detail="Folder not found")
    folders_db[folder_id]["title"] = folder_data.title
    folders_db[folder_id]["description"] = folder_data.description
    return {"success": True, "message": "Folder updated successfully."}

# Delete folder endpoint
@router.delete("/api/folders/{folder_id}/", response_model=FolderUpdateResponse)
def delete_folder(folder_id: str):
    if folder_id not in folders_db:
        raise HTTPException(status_code=404, detail="Folder not found")
    del folders_db[folder_id]
    return {"success": True, "message": "Folder successfully deleted."}
