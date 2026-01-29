import os
from dotenv import load_dotenv
from endee import Endee
from langchain_openai import OpenAIEmbeddings, OpenAI

load_dotenv()

ENDEE_URL = os.getenv("ENDEE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = Endee()
client.set_base_url(ENDEE_URL)
index = client.get_index("finance")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

llm = OpenAI(temperature=0)

def query_finance(question, top_k=5):
    vector = embeddings.embed_query(question)
    results = index.query(vector=vector, top_k=top_k)

    if not results:
        return "No data found. Fetch company data first."

    context = "\n".join(r["meta"]["text"] for r in results)

    prompt = f"""
Context:
{context}

Question:
{question}

Answer:
"""

    return llm(prompt)
