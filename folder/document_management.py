# from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, APIRouter
# from fastapi.security import OAuth2PasswordBearer
# from uuid import uuid4
# import pdfplumber
# from pydantic import BaseModel
# from typing import Optional, Dict

# router = APIRouter()

# # Placeholder for OAuth2
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # Placeholder function for user validation
# def get_current_user(token: str = Depends(oauth2_scheme)):
#     return {"user_id": "user123", "role": "Administrator"}

# # Data models
# class Document(BaseModel):
#     documentId: str
#     pages: Dict[str, str]

# # Database simulation
# database = {}

# @router.post("/upload")
# async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
#     if user['role'] not in ['Contributor', 'Administrator']:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     if file.content_type != 'application/pdf':
#         raise HTTPException(status_code=400, detail="Invalid file format")

#     document_id = str(uuid4())
#     text_pages = {}

#     with pdfplumber.open(file.file) as pdf:
#         for i, page in enumerate(pdf.pages):
#             text_pages[str(i+1)] = page.extract_text()

#     database[document_id] = Document(documentId=document_id, pages=text_pages)
#     return {"success": True, "message": "Document successfully uploaded and processed by OCR", "documentId": document_id}

# @router.post("/{documentId}/classify")
# async def classify_document(documentId: str, user: dict = Depends(get_current_user)):
#     if user['role'] not in ['Contributor', 'Administrator']:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     document = database.get(documentId)
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")

#     document_type = "Type based on content analysis"
#     database[documentId].type = document_type
#     return {"success": True, "message": "Document classified successfully.", "classification": {"typeDocument": document_type, "tags": ["Tag1", "Tag2"]} }

# @router.post("/{documentId}/extract")
# async def extract_information(documentId: str, user: dict = Depends(get_current_user)):
#     if user['role'] not in ['Contributor', 'Administrator']:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     document = database.get(documentId)
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")

#     extracted_data = {"key_info": "Extracted information based on rules"}
#     return {"success": True, "message": "Information extracted successfully.", "extractedData": extracted_data}

# @router.get("/{documentId}")
# async def retrieve_document(documentId: str, includeContent: Optional[bool] = False, user: dict = Depends(get_current_user)):
#     if user['role'] not in ['Contributor', 'Administrator']:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     document = database.get(documentId)
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")

#     response = {"documentId": document.documentId, "name": "DocumentName.pdf", "metadata": {}}
#     if includeContent:
#         response["content"] = document.pages
#     return response



from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, APIRouter, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timedelta
from uuid import uuid4
import pdfplumber

router = APIRouter()

# Constants for JWT
SECRET_KEY = "your_secret_key"  # Consider using environment variables for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # Simulated user database
# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": pwd_context.hash("secret"),
#         "disabled": False,
#     }
# }


# Simulated user database with plain passwords
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "secret",  # Storing the password in plain text
        "disabled": False,
    }
}


class Document(BaseModel):
    documentId: str
    pages: Dict[str, str]

database = {}

# Authentication and Security Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        return db[username]
    return None

# def authenticate_user(fake_db, username: str, password: str):
#     user = get_user(fake_db, username)
#     if not user:
#         return False
#     if not verify_password(password, user['hashed_password']):
#         return False
#     return user

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    # Direct comparison of plaintext passwords
    if user['password'] != password:
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user = get_user(fake_users_db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Token Endpoint
@router.post("/token", include_in_schema=True)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user['username']}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Example Protected Route
@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    document_id = str(uuid4())
    text_pages = {}
    with pdfplumber.open(file.file) as pdf:
        for i, page in enumerate(pdf.pages):
            text_pages[str(i+1)] = page.extract_text()
    database[document_id] = Document(documentId=document_id, pages=text_pages)
    return {"success": True, "message": "Document uploaded and processed", "documentId": document_id}

# Further document management routes would also use the get_current_user dependency.
