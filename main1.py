import tempfile
import PyPDF2
import pytesseract
from PIL import Image
import re
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json  # Import the json module to work with json data
import openai
import pdfplumber
from models import DocumentType, ExtractionRule, FolderCreate, FolderResponse
from bson import ObjectId
import uuid
import fitz  # Alias for PyMuPDF
from folder.folder_management import router as folder_management_router
from folder.document_management import router as document_router



# Initialize FastAPI app and load environment variables
app = FastAPI()
load_dotenv()

# Set up MongoDB connection and OpenAI API Key
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
collection = db[os.getenv("COLLECTION_NAME")]
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET", "POST","DELETE","OPTIONS"], allow_headers=["*"])

# Updated costs per token
COST_PER_INPUT_TOKEN = 0.00003  # $0.00003 per token for input


# Function to calculate metrics
def calculate_metrics_and_cost(text):
    estimated_tokens = len(text.split())
    word_count = len(text.split())
    char_count = len(text)
    # Calculate cost based on input tokens only for simplicity
    cost_input = estimated_tokens * COST_PER_INPUT_TOKEN
    return estimated_tokens, word_count, char_count, cost_input

# Helper function to safely convert string to ObjectId
def convert_to_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")


def extract_structured_info(text):
    try:
        # The schema is now directly included within this function for use in guiding the extraction.
        schema = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Schema d'un contrat d'assurance",
  "type": "object",
  "properties": {
    "compagnie_assurance": {
      "type": "object",
      "properties": {
        "nom": {
          "type": "string"
        },
        "adresse": {
          "type": "string"
        }
      },
      "required": ["nom", "adresse"]
    },
    "assure": {
      "type": "object",
      "properties": {
        "nom": {
          "type": "string"
        },
        "adresse": {
          "type": "string"
        },
        "SIRET": {
          "type": "string"
        }
      },
      "required": ["nom", "adresse", "SIRET"]
    },
    "courtier": {
      "type": "object",
      "properties": {
        "nom": {
          "type": "string"
        },
        "adresse": {
          "type": "string"
        },
        "ORIAS": {
          "type": "string"
        },
        "date_delivrance_attestation": {
          "type": "string",
          "format": "date"
        }
      },
      "required": ["nom", "adresse", "ORIAS", "date_delivrance_attestation"]
    },
    "contrat": {
      "type": "object",
      "properties": {
        "numero": {
          "type": "string"
        },
        "date_effet": {
          "type": "string",
          "format": "date"
        },
        "periode_validite": {
          "type": "object",
          "properties": {
            "debut": {
              "type": "string",
              "format": "date"
            },
            "fin": {
              "type": "string",
              "format": "date"
            }
          },
          "required": ["debut", "fin"]
        }
      },
      "required": ["numero", "date_effet", "periode_validite"]
    },
    "activites_assurees": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["compagnie_assurance", "assure", "courtier", "contrat", "activites_assurees"]
}
         # Convert your schema into the format needed for the GPT prompt.
        prompt = """
        Convertissez cette attestation d'assurance décennale en un objet JSON selon le schéma défini ci-dessous. Ne sortez pas le schéma lui-même, mais transformez
        les données de l'attestation en un objet JSON représentant le schéma. Assurez-vous de formater les dates au format aaaa-mm-jj et de sortir tous les montants uniquement
        en chiffres sans la devise. """

        schema = json.dumps(schema, indent=2)

        # Now concatenate using the string representation of schema
        prompt = schema + "\n---\n" + text

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        # Your existing code for handling the response
        extracted_info = response.choices[0].message['content'] if response.choices else "No structured information could be extracted."
        return extracted_info
    except Exception as e:
        return f"An error occurred while extracting structured information: {str(e)}"




# Function to extract text from an image
def extract_text_from_image(file_path):
    return pytesseract.image_to_string(Image.open(file_path), lang='fra')


# # Placeholder function for document classification Classification de document --
# def classify_document(content):
#     # Placeholder classification function using dummy data
#     return {"typeDocument": "Dummy Type", "tags": ["Tag1", "Tag2"]}


# async def classify_document(document_id: str) -> dict:
#     # Simulate classification process
#     # In a real application, use your classification logic here
#     type_document = "Type de document"
#     tags = ["Tag1", "Tag2"]
#     cost = 0.10  # Assuming a fixed cost for classification

#     return {
#         "typeDocument": type_document,
#         "tags": tags,
#         "coutTraitement": cost
#     }




# Enhanced OCR settings for images
def ocr_image(image_path):
    image = Image.open(image_path)
    # Improve OCR by configuring pytesseract
    custom_config = r'--oem 3 --psm 6'  # OEM 3 uses both legacy and LSTM OCR engine, PSM 6 assumes a single uniform block of text.
    return pytesseract.image_to_string(image, config=custom_config)

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    pages_text = {}
    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or "Texte non disponible"
            pages_text[str(page_number)] = page_text
    return pages_text


@app.post("/api/document-types", status_code=status.HTTP_201_CREATED)
async def add_document_type(doc_type: DocumentType):
    try:
        doc_type_id = db.document_types.insert_one(doc_type.dict()).inserted_id
        return {"success": True, "message": "Type de document ajouté avec succès.", "typeId": str(doc_type_id)}
    except Exception as e:
        error_message = "Erreur lors de l'ajout du type de document. " + str(e)
        raise HTTPException(status_code=400, detail={"success": False, "error": error_message})


# Endpoint to delete a document type
@app.delete("/api/document-types/{typeId}", status_code=status.HTTP_200_OK)
async def delete_document_type(typeId: str):
    object_id = convert_to_object_id(typeId)
    result = db.document_types.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document type not found")
    return {"success": True, "message": "Type de document supprimé avec succès."}


# Endpoint to add an extraction rule to a document type
@app.post("/api/document-types/{typeId}/extraction-rules", status_code=status.HTTP_201_CREATED)
async def add_extraction_rule(typeId: str, rule: ExtractionRule):
    rule_id = db.extraction_rules.insert_one({**rule.dict(), "typeId": typeId}).inserted_id
    return {"success": True, "message": "Règle d'extraction ajoutée avec succès.", "ruleId": str(rule_id)}


# Endpoint to delete an extraction rule from a document type
@app.delete("/api/document-types/{typeId}/extraction-rules/{ruleId}", status_code=status.HTTP_200_OK)
async def delete_extraction_rule(typeId: str, ruleId: str):
    rule_object_id = convert_to_object_id(ruleId)
    # Notice here we are no longer converting typeId to an ObjectId
    result = db.extraction_rules.delete_one({
        "_id": rule_object_id,
        "typeId": typeId  # This is used as a string directly since that's how it's stored
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message d'erreur explicatif.")
    return {"success": True, "message": "Règle d'extraction supprimée avec succès."}



# Include the routers from folder_management.py
app.include_router(folder_management_router)



# Include the document management router
app.include_router(document_router, prefix="/api/documents", tags=["Document Management"])
















