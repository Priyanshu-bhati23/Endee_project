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

INDEX_NAME = "finance"

client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

def ensure_index():
    """
    Ensure index exists.
    If it already exists, safely reuse it.
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
        # Index already exists — this is OK
        print(f"ℹ️ Index '{INDEX_NAME}' already exists, reusing it")

    return client.get_index(INDEX_NAME)

def fetch_and_upsert(companies):
    index = ensure_index()

    today = datetime.today()
    week_ago = today - timedelta(days=7)

    for company in companies:
        print(f"📡 Fetching {company}")
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={company}&from={week_ago.date()}&to={today.date()}&token={FINNHUB_API_KEY}"
        )

        articles = requests.get(url).json()
        vectors = []

        for art in tqdm(articles, desc=company):
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
def delete_index():
    """
    Delete the Endee index completely.
    Safe to call even if index does not exist.
    """
    existing_indexes = client.list_indexes()
    if INDEX_NAME in existing_indexes:
        client.delete_index(INDEX_NAME)
        print(f"🗑️ Deleted index '{INDEX_NAME}'")
        return True
    else:
        print("ℹ️ Index does not exist, nothing to delete")
        return False
