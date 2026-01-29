import os
from dotenv import load_dotenv
from endee import Endee
from langchain_openai import OpenAIEmbeddings, OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENDEE_URL = os.getenv("ENDEE_URL")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
llm = OpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0)

client = Endee()
client.set_base_url(ENDEE_URL)
INDEX_NAME = "finance"

def query_finance(question: str, top_k: int = 5):
    try:
        index = client.get_index(INDEX_NAME)
    except:
        return "Index not found. Please fetch data first."

    query_vector = embeddings.embed_query(question)
    results = index.query(vector=query_vector, top_k=top_k)

    if not results:
        return "No relevant documents found. Please fetch data first."

    context = "\n".join(r["meta"]["text"] for r in results)

    prompt = f"""
You are a financial analyst.

Context:
{context}

Question:
{question}

Answer:
"""
    return llm(prompt)
