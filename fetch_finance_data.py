# fetch_finance_data.py

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tqdm import tqdm
from endee import Endee, Precision
from langchain_openai import OpenAIEmbeddings
from utils import chunk_text, parse_pdf
from endee.exceptions import ConflictException

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ENDEE_URL = os.getenv("ENDEE_URL")  # e.g., http://endee:8080/api/v1 in Docker / Render

if not OPENAI_API_KEY or not FINNHUB_API_KEY or not ENDEE_URL:
    raise ValueError("Missing one of: OPENAI_API_KEY, FINNHUB_API_KEY, ENDEE_URL in .env")

# -----------------------------
# Constants
# -----------------------------
INDEX_NAME = "finance"

# -----------------------------
# Initialize Endee client & embeddings
# -----------------------------
client = Endee()
client.set_base_url(ENDEE_URL)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

# -----------------------------
# Ensure index exists (safe to call multiple times)
# -----------------------------
def ensure_index():
    """
    Create the index if it doesn't exist.
    If it already exists, just return it.
    """
    try:
        client.create_index(
            name=INDEX_NAME,
            dimension=1536,
            space_type="cosine",
            precision=Precision.INT8D
        )
        print(f"✅ Created index '{INDEX_NAME}'")
    except ConflictException:
        # Index already exists — safe to reuse
        print(f"ℹ️ Index '{INDEX_NAME}' already exists, reusing it")
    return client.get_index(INDEX_NAME)

# -----------------------------
# Fetch news & upsert to Endee
# -----------------------------
def fetch_and_upsert(companies):
    """
    Fetch news for the given companies and upsert into Endee.
    """
    if not companies:
        print("⚠️ No companies provided. Skipping fetch.")
        return

    index = ensure_index()
    today = datetime.today()
    week_ago = today - timedelta(days=7)

    for company in companies:
        print(f"\n📡 Fetching news for {company}...")
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={company}&from={week_ago.date()}&to={today.date()}&token={FINNHUB_API_KEY}"
        )

        try:
            articles = requests.get(url).json()
        except Exception as e:
            print(f"⚠️ Failed to fetch news for {company}: {e}")
            continue

        vectors = []
        for art in tqdm(articles, desc=f"{company} news"):
            text = f"{art.get('headline','')} {art.get('summary','')}"
            for i, chunk in enumerate(chunk_text(text)):
                vectors.append({
                    "id": f"{company}_{art.get('id','x')}_{i}",
                    "vector": embeddings.embed_query(chunk),
                    "meta": {
                        "company": company,
                        "text": chunk,
                        "source": art.get("source")
                    }
                })

        if vectors:
            index.upsert(vectors)
            print(f"✅ Upserted {len(vectors)} chunks for {company}")

    # -----------------------------
    # Optional: Ingest PDFs from data/ folder
    # -----------------------------
    pdf_folder = "data"
    if os.path.exists(pdf_folder):
        pdf_files = [f"{pdf_folder}/{f}" for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
        for pdf in pdf_files:
            print(f"\n📄 Processing PDF: {pdf}")
            text = parse_pdf(pdf)
            vectors = []
            for i, chunk in enumerate(chunk_text(text)):
                vectors.append({
                    "id": f"{os.path.basename(pdf)}_{i}",
                    "vector": embeddings.embed_query(chunk),
                    "meta": {
                        "company": os.path.basename(pdf).split("_")[0],
                        "text": chunk
                    }
                })
            if vectors:
                index.upsert(vectors)
                print(f"✅ Upserted {len(vectors)} chunks from PDF {pdf}")

    print("\n🎉 Data fetching and upsert complete!")

# -----------------------------
# Delete index
# -----------------------------
def delete_index():
    """
    Delete the Endee index completely.
    Safe to call even if it doesn't exist.
    """
    existing_indexes = client.list_indexes()
    if INDEX_NAME in existing_indexes:
        client.delete_index(INDEX_NAME)
        print(f"🗑️ Deleted index '{INDEX_NAME}'")
        return True
    else:
        print("ℹ️ Index does not exist, nothing to delete")
        return False
