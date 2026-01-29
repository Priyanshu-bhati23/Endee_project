# app.py
import streamlit as st
from fetch_finance_data import fetch_and_upsert, delete_index
from query_finance import query_finance

st.title("💹 Finance RAG Chatbot")

companies_input = st.text_input("Company symbols", "TSLA,AAPL")

if st.button("Fetch Data"):
    companies = [c.strip().upper() for c in companies_input.split(",") if c.strip()]
    with st.spinner("Fetching and indexing data..."):
        fetch_and_upsert(companies)
    st.success("✅ Data indexed successfully")

question = st.text_input("Ask a finance question")

if question:
    with st.spinner("Thinking..."):
        answer = query_finance(question)
    st.subheader("Answer")
    st.write(answer)

if st.button("🗑️ Clear Vector Database"):
    with st.spinner("Deleting Endee index..."):
        deleted = delete_index()
    if deleted:
        st.success("Index cleared.")
    else:
        st.info("Index was already empty.")
