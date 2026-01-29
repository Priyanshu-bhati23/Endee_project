import streamlit as st
from fetch_finance_data import fetch_and_upsert, delete_index
from query_finance import query_finance

st.set_page_config(page_title="Finance RAG Chatbot", layout="wide")
st.title("💹 Finance RAG Chatbot")

# Fetch data section
companies_input = st.text_input("Company symbols (comma-separated):", "TSLA,AAPL")

if st.button("Fetch Data"):
    companies = [c.strip().upper() for c in companies_input.split(",") if c.strip()]
    if companies:
        with st.spinner("Fetching and indexing data..."):
            fetch_and_upsert(companies)
        st.success("✅ Data indexed successfully")
    else:
        st.warning("Please enter at least one company symbol.")

st.divider()

# Ask questions section
question = st.text_input("Ask a finance question:")

if question:
    with st.spinner("Querying Endee + generating answer..."):
        answer = query_finance(question)
    st.subheader("Answer:")
    st.write(answer)

st.divider()

# Clear index section
st.subheader("⚠️ Maintenance")
if st.button("🗑️ Clear Vector Database"):
    with st.spinner("Deleting Endee index..."):
        deleted = delete_index()
    if deleted:
        st.success("Index cleared. You can fetch fresh data now.")
    else:
        st.info("Index was already empty.")
