# fetch_finance_data.py
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tqdm import tqdm
from endee import Endee, Precision
from langchain_openai import OpenAIEmbeddings
from endee.exceptions import ConflictException
from utils import chunk_text

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ENDEE_URL = os.getenv("ENDEE_URL")

if not all([OPENAI_API_KEY, FINNHUB_API_KEY, ENDEE_URL]):
    raise ValueError("Missing environment variables")

INDEX_NAME = "finance"

client = Endee()
client.set_base_url(ENDEE_URL)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

def ensure_index():
    try:
        client.create_index(
            name=INDEX_NAME,
            dimension=1536,
            space_type="cosine",
            precision=Precision.INT8D
        )
        print(f"Created index {INDEX_NAME}")
    except ConflictException:
        print("Index already exists, reusing")

    return client.get_index(INDEX_NAME)

def fetch_and_upsert(companies):
    index = ensure_index()

    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)

    for company in companies:
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={company}&from={week_ago.date()}&to={today.date()}"
            f"&token={FINNHUB_API_KEY}"
        )

        articles = requests.get(url, timeout=20).json()
        vectors = []

        for art in articles:
            text = f"{art.get('headline','')} {art.get('summary','')}"
            for i, chunk in enumerate(chunk_text(text)):
                vectors.append({
                    "id": f"{company}_{art.get('id','x')}_{i}",
                    "vector": embeddings.embed_query(chunk),
                    "meta": {
                        "company": company,
                        "text": chunk
                    }
                })

        if vectors:
            index.upsert(vectors)
