import streamlit as st
from fetch_finance_data import fetch_and_upsert, delete_index
from query_finance import query_finance

st.set_page_config(page_title="💹 Finance RAG Chatbot", layout="wide")
st.title("💹 Finance RAG Chatbot")

# ---------------- Fetch Data ----------------
st.subheader("Fetch Company News & PDFs")
companies_input = st.text_input("Enter company symbols (comma-separated)", "TSLA,AAPL")
if st.button("Fetch Data"):
    companies = [c.strip().upper() for c in companies_input.split(",") if c.strip()]
    with st.spinner("Fetching and indexing data..."):
        fetch_and_upsert(companies)
    st.success("✅ Data indexed successfully!")

st.divider()

# ---------------- Ask Question ----------------
st.subheader("Ask a Finance Question")
question = st.text_input("Type your question here")
if question:
    with st.spinner("Generating answer..."):
        answer = query_finance(question)
    st.write("**Answer:**")
    st.write(answer)

st.divider()

# ---------------- Clear Index ----------------
st.subheader("Maintenance")
if st.button("🗑️ Clear Vector Database"):
    with st.spinner("Deleting Endee index..."):
        deleted = delete_index()
    if deleted:
        st.success("Index cleared. You can fetch fresh data now.")
    else:
        st.info("Index was already empty.")
