# utils.py

from PyPDF2 import PdfReader

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks of chunk_size with overlap.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def parse_pdf(file_path):
    """
    Read PDF and return all text.
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
