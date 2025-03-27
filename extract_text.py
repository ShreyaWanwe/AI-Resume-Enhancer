import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text")
        if text.strip():  
            extracted_text += text + "\n"
        else:  
            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
            for image in images:
                extracted_text += pytesseract.image_to_string(image) + "\n"

    return extracted_text.strip()

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)

def extract_text(file_path, file_type):
    if file_type in ["pdf"]:
        return extract_text_from_pdf(file_path)
    elif file_type in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file format."

if __name__ == "__main__":
    print(extract_text("sample_resume.pdf", "pdf"))
    print(extract_text("sample_resume.png", "png"))
