from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import jwt

# Initialize FastAPI app and load environment variables
app = FastAPI()
load_dotenv()

# Set up MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
collection = db[os.getenv("COLLECTION_NAME")]

# JWT authentication setup
security = HTTPBearer()

class ClassificationResult(BaseModel):
    typeDocument: str
    tags: List[str]

# Authentication function using JWT token
async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Your authentication logic here
    token = credentials.credentials
    # Decode and verify JWT token
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        # Your permission logic here if needed
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.InvalidTokenError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.post("/api/documents/{documentId}/classify")
async def classify_document(
    documentId: str,
    token: str = Depends(authenticate_user)
):
    # Your logic to retrieve document from database
    document = collection.find_one({"_id": documentId})
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Your logic to classify the document (using OpenAI LLM model or any other method)
    # For now, let's assume we have a dummy classification result
    classification_result = ClassificationResult(typeDocument="DummyType", tags=["Tag1", "Tag2"])

    # Your logic to update document information in the database with the classification results
    # For now, let's just print the classification result
    print("Document classified:", classification_result)

    # Return the classification result
    return {
        "success": True,
        "message": "Document classified successfully.",
        "classification": classification_result.dict(),
        "costProcessing": 0.10  # You can calculate and include processing cost here
    }


