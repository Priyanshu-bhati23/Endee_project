from pypdf import PdfReader

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def parse_pdf(path):
    reader = PdfReader(path)
    return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
