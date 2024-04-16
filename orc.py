import pytesseract
from PIL import Image
from fastapi import FastAPI

app = FastAPI()

# Path to the image file
image_path = "image.png"

# Open the image
image = Image.open(image_path)

# Use OCR to extract text from the image
extracted_text = pytesseract.image_to_string(image)

# Print the extracted text
print(extracted_text)