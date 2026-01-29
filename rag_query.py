import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from endee import Endee, Precision
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from utils import chunk_text, parse_pdf

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not OPENAI_API_KEY or not FINNHUB_API_KEY:
    raise ValueError("Missing OpenAI or Finnhub API key in .env")

# Endee client
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")
INDEX_NAME = "finance_docs"

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

def reset_index():
    """Delete existing index and create a fresh one."""
    existing_indexes = client.list_indexes()
    if INDEX_NAME in existing_indexes:
        client.delete_index(INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")
    client.create_index(
        name=INDEX_NAME,
        dimension=1536,
        space_type="cosine",
        precision=Precision.INT8D
    )
    print(f"Created new index: {INDEX_NAME}")

def fetch_and_upsert(companies):
    """Fetch news for companies and upsert into Endee."""
    if not companies:
        print("No companies provided. Skipping fetch.")
        return

    # Ensure index exists
    existing_indexes = client.list_indexes()
    if INDEX_NAME not in existing_indexes:
        client.create_index(
            name=INDEX_NAME,
            dimension=1536,
            space_type="cosine",
            precision=Precision.INT8D
        )
        print(f"✅ Created index '{INDEX_NAME}'")
    else:
        print(f"✅ Index '{INDEX_NAME}' exists")

    index = client.get_index(INDEX_NAME)

    today = datetime.today()
    one_week_ago = today - timedelta(days=7)

    # Fetch news
    for company in companies:
        print(f"Fetching news for {company}...")
        url = f"https://finnhub.io/api/v1/company-news?symbol={company}&from={one_week_ago.date()}&to={today.date()}&token={FINNHUB_API_KEY}"
        try:
            news_items = requests.get(url).json()
        except:
            print(f"Failed to fetch news for {company}")
            continue

        vectors = []
        for item in tqdm(news_items, desc=f"{company} news"):
            text = item.get("headline", "") + ". " + item.get("summary", "")
            for i, chunk in enumerate(chunk_text(text)):
                vector = embeddings.embed_query(chunk)
                vectors.append({
                    "id": f"{item.get('id', company)}_{i}",
                    "vector": vector,
                    "meta": {"company": company, "date": item.get("datetime"), "text": chunk, "source": item.get("source")}
                })
        if vectors:
            index.upsert(vectors)
            print(f"Upserted {len(vectors)} chunks for {company}")

    # Optional: PDFs
    pdf_folder = "data"
    if os.path.exists(pdf_folder):
        for pdf in [f"{pdf_folder}/{f}" for f in os.listdir(pdf_folder) if f.endswith(".pdf")]:
            text = parse_pdf(pdf)
            vectors = []
            for i, chunk in enumerate(chunk_text(text)):
                vector = embeddings.embed_query(chunk)
                vectors.append({
                    "id": f"{os.path.basename(pdf)}_{i}",
                    "vector": vector,
                    "meta": {"company": os.path.basename(pdf).split("_")[0], "text": chunk}
                })
            if vectors:
                index.upsert(vectors)
                print(f"Upserted {len(vectors)} chunks from {pdf}")
