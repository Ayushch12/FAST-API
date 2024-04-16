# # models.py

# from pydantic import BaseModel
# from typing import Optional
# from uuid import UUID

# class DocumentType(BaseModel):
#     userId: UUID
#     name: str
#     abbreviation: str
#     definition: str

# class UpdateDocumentType(BaseModel):
#     name: Optional[str] = None
#     abbreviation: Optional[str] = None
#     definition: Optional[str] = None


# models.py
from pydantic import BaseModel
from typing import Optional
from typing import List

class DocumentType(BaseModel):
    userId: str
    name: str
    abbreviation: str
    definition: str

class ExtractionRule(BaseModel):
    userId: str
    fieldName: str
    pattern: str
    type: str
    multiplicity: str

#FOLDER :
class FolderResponse(BaseModel):
    success: bool
    message: str
    folderId: str


# Request and Response models
class FolderCreate(BaseModel):
    userId: str
    title: str
    description: str

class FolderCreateResponse(BaseModel):
    success: bool
    message: str
    folderId: str

class DocumentInFolder(BaseModel):
    name: str
    content_type: str

class DocumentCreateResponse(BaseModel):
    documentId: str
    name: str
    content_type: str

class FolderUpdate(BaseModel):
    title: str
    description: str

class FolderUpdateResponse(BaseModel):
    success: bool
    message: str


