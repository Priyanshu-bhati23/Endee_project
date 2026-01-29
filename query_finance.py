import os
from dotenv import load_dotenv
from endee import Endee
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()

INDEX_NAME = "finance"

client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

def query_finance(question, top_k=5):
    index = client.get_index(INDEX_NAME)

    query_vector = embeddings.embed_query(question)
    results = index.query(vector=query_vector, top_k=top_k)

    if not results:
        return "No data found. Please fetch company data first."

    context = "\n\n".join(r["meta"]["text"] for r in results)

    prompt = f"""
You are a financial analyst.

Context:
{context}

Question:
{question}

Answer:
"""

    return llm.invoke(prompt).content.strip()
