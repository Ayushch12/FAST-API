import tempfile
import PyPDF2
import pytesseract
import re
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json  # Import the json module to work with json data
import openai
import pdfplumber
from fastapi import FastAPI





# Initialize FastAPI app and load environment variables
# diuhso
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


# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Function to extract text from an image
def extract_text_from_image(file_path):
    return pytesseract.image_to_string(Image.open(file_path), lang='fra')



# Endpoint to handle file uploads and process them for structured JSON output
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name

        # content_type = file.content_type
        # text = extract_text_from_pdf(temp_file_path) if content_type == "application/pdf" else pytesseract.image_to_string(Image.open(temp_file_path))
            
            content_type = file.content_type
        if content_type == "application/pdf":
            text = extract_text_from_pdf(temp_file_path)
        else:  # Assume any non-PDF is an image for simplicity; refine as needed
            text = extract_text_from_image(temp_file_path)
            

         # Calculate metrics
        estimated_tokens, word_count, char_count,cost_input = calculate_metrics_and_cost(text)

        # Extract structured information
        structured_info = extract_structured_info(text)

        json_response = {
            "filename": file.filename,
            "original_text": text,
            "structured_info": structured_info,  # This will be a string that looks like JSON; consider parsing it if necessary
             "estimated_tokens": estimated_tokens,
            "word_count": word_count,
            "char_count": char_count,
            "cost_input": cost_input  # Add the calculated input cost here
        }
        insert_result = collection.insert_one(json_response)
        json_response['_id'] = str(insert_result.inserted_id)
        os.unlink(temp_file_path)  # Clean up the temporary file
        return json_response
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
    

 













