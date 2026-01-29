import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tqdm import tqdm
from endee import Endee, Precision
from langchain_openai import OpenAIEmbeddings
from utils import chunk_text, parse_pdf
from endee.exceptions import ConflictException

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ENDEE_URL = os.getenv("ENDEE_URL")

INDEX_NAME = "finance"

client = Endee()
client.set_base_url(ENDEE_URL)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

def ensure_index():
    """Create or reuse Endee index."""
    try:
        client.create_index(
            name=INDEX_NAME,
            dimension=1536,
            space_type="cosine",
            precision=Precision.INT8D
        )
        print(f"✅ Created index '{INDEX_NAME}'")
    except ConflictException:
        print(f"ℹ️ Index '{INDEX_NAME}' already exists, reusing it")
    return client.get_index(INDEX_NAME)

def fetch_and_upsert(companies):
    """Fetch news & PDFs for given companies and upsert into Endee."""
    index = ensure_index()

    today = datetime.today()
    one_week_ago = today - timedelta(days=7)

    # Fetch company news
    for company in companies:
        print(f"📡 Fetching news for {company}...")
        url = f"https://finnhub.io/api/v1/company-news?symbol={company}&from={one_week_ago.date()}&to={today.date()}&token={FINNHUB_API_KEY}"
        try:
            news_items = requests.get(url).json()
        except Exception as e:
            print(f"⚠️ Failed to fetch news for {company}: {e}")
            continue

        vectors = []
        for item in tqdm(news_items, desc=f"{company} news"):
            text = item.get("headline", "") + ". " + item.get("summary", "")
            for i, chunk in enumerate(chunk_text(text)):
                vectors.append({
                    "id": f"{company}_{item.get('id','x')}_{i}",
                    "vector": embeddings.embed_query(chunk),
                    "meta": {
                        "company": company,
                        "text": chunk,
                        "source": item.get("source")
                    }
                })

        if vectors:
            index.upsert(vectors)
            print(f"✅ Upserted {len(vectors)} chunks for {company}")

    # Optional: ingest PDFs
    pdf_folder = "data"
    if os.path.exists(pdf_folder):
        pdf_files = [f"{pdf_folder}/{f}" for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
        for pdf in pdf_files:
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

def delete_index():
    """Delete the Endee index completely."""
    existing_indexes = client.list_indexes()
    if INDEX_NAME in existing_indexes:
        client.delete_index(INDEX_NAME)
        print(f"🗑️ Deleted index '{INDEX_NAME}'")
        return True
    else:
        print("ℹ️ Index does not exist, nothing to delete")
        return False
