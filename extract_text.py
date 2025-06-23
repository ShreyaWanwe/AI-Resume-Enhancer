import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import os
from io import BytesIO
import tempfile

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file path"""
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

    doc.close()
    return extracted_text.strip()

def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from PDF bytes (for uploaded files)"""
    doc = fitz.open(stream=pdf_bytes)
    extracted_text = ""

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text")
        if text.strip():  
            extracted_text += text + "\n"
        else:  
            # For scanned PDFs, use OCR
            try:
                images = convert_from_bytes(pdf_bytes, first_page=page_num+1, last_page=page_num+1)
                for image in images:
                    extracted_text += pytesseract.image_to_string(image) + "\n"
            except Exception as e:
                print(f"OCR failed for page {page_num + 1}: {e}")

    doc.close()
    return extracted_text.strip()

def extract_text_from_image(image_path):
    """Extract text from image file path"""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)

def extract_text_from_image_bytes(image_bytes):
    """Extract text from image bytes (for uploaded files)"""
    image = Image.open(BytesIO(image_bytes))
    return pytesseract.image_to_string(image)

def extract_text_from_uploaded_file(uploaded_file):
    """
    Extract text from Streamlit uploaded file object
    This is the function that was missing!
    """
    try:
        file_bytes = uploaded_file.getvalue()
        file_type = uploaded_file.type
        
        if file_type == "application/pdf":
            return extract_text_from_pdf_bytes(file_bytes)
        elif file_type in ["image/jpeg", "image/jpg", "image/png"]:
            return extract_text_from_image_bytes(file_bytes)
        elif file_type == "text/plain":
            return file_bytes.decode("utf-8")
        else:
            return f"Unsupported file format: {file_type}"
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_text(file_path, file_type):
    """Extract text from file path (original function)"""
    if file_type in ["pdf"]:
        return extract_text_from_pdf(file_path)
    elif file_type in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file format."

if __name__ == "__main__":
    # Test with file paths
    print("Testing with file paths:")
    print(extract_text("sample_resume.pdf", "pdf"))
    print(extract_text("sample_resume.png", "png"))
