import streamlit as st
import yfinance as yf
import pandas as pd
from fetch_finance_data import fetch_and_upsert, delete_index
from query_finance import query_finance

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Finance Insight Dashboard",
    layout="wide",
    page_icon="💹"
)

# ---------------------------
# Sidebar: Trending Stocks
# ---------------------------
TRENDING_STOCKS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NFLX", "NVDA"]
st.sidebar.markdown("<h2 style='text-align:center; color:#2F4F4F;'>Trending Stocks</h2>", unsafe_allow_html=True)
st.sidebar.write("")
for stock in TRENDING_STOCKS:
    st.sidebar.button(stock)

# ---------------------------
# Header
# ---------------------------
st.markdown(
    """
    <div style='text-align: center; padding:20px; background-color:#F5F5F5; border-radius:10px;'>
        <h1 style='color: #2F4F4F;'>💹 Finance Insight Dashboard</h1>
        <p style='font-size:16px; color:#555;'>Compare, Analyze, and Ask Questions About Trending Stocks</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------
# Tabs for organization
# ---------------------------
tab_fetch, tab_query, tab_compare, tab_clear = st.tabs(
    ["📈 Fetch & Index Data", "💬 Ask Questions", "📊 Compare Stocks", "⚠️ Maintenance"]
)

# ---------------------------
# Tab 1: Fetch & Index Data
# ---------------------------
with tab_fetch:
    st.subheader("Fetch Latest Company Data")
    st.markdown("Enter stock symbols (comma-separated) and fetch the latest news to index into Endee.")

    companies_input = st.text_input("Company symbols", "TSLA,AAPL")
    fetch_button = st.button("📡 Fetch & Index Data", key="fetch_data")

    if fetch_button:
        companies = [c.strip().upper() for c in companies_input.split(",") if c.strip()]
        if not companies:
            st.warning("Please enter at least one company symbol.")
        else:
            with st.spinner("Fetching and indexing data..."):
                fetch_and_upsert(companies)
            st.success("✅ Data indexed successfully")

# ---------------------------
# Tab 2: Ask Questions
# ---------------------------
with tab_query:
    st.subheader("Ask a Question About Companies")
    question = st.text_input("Type your question here:", key="query_input")
    ask_button = st.button("🤖 Get Answer", key="ask_question")

    if ask_button and question:
        with st.spinner("Fetching answer from Endee + OpenAI..."):
            answer = query_finance(question)
        st.markdown(
            f"""
            <div style='background-color:#F0F8FF; padding:20px; border-radius:10px; box-shadow: 2px 2px 5px #ccc;'>
                <h4>Answer:</h4>
                <p>{answer}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------
# Tab 3: Compare Stocks
# ---------------------------
with tab_compare:
    st.subheader("Compare Stock Prices")

    col1, col2 = st.columns(2)
    with col1:
        stock1 = st.selectbox("Select first stock", TRENDING_STOCKS, index=0)
    with col2:
        stock2 = st.selectbox("Select second stock", TRENDING_STOCKS, index=1)

    compare_button = st.button("📊 Show Comparison")

    if compare_button:
        with st.spinner("Fetching stock data..."):
            data1 = yf.download(stock1, period="3mo", interval="1d")
            data2 = yf.download(stock2, period="3mo", interval="1d")

        st.markdown(f"<h3 style='text-align:center;'>📈 {stock1} vs {stock2} Stock Prices (Last 3 Months)</h3>", unsafe_allow_html=True)
        st.line_chart(pd.DataFrame({
            stock1: data1["Close"],
            stock2: data2["Close"]
        }))

        st.markdown("### 🔹 Stock Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{stock1}**")
            st.dataframe(data1.tail().style.set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#F5F5F5')]},
                {'selector': 'td', 'props': [('padding', '5px')]}
            ]))
        with col2:
            st.markdown(f"**{stock2}**")
            st.dataframe(data2.tail().style.set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#F5F5F5')]},
                {'selector': 'td', 'props': [('padding', '5px')]}
            ]))

# ---------------------------
# Tab 4: Clear Index
# ---------------------------
with tab_clear:
    st.subheader("⚠️ Clear Vector Database")
    st.markdown(
        "Use this only if you want to delete the entire Endee index and fetch fresh data."
    )

    clear_button = st.button("🗑️ Clear Endee Index", key="clear_index")
    if clear_button:
        with st.spinner("Deleting Endee index..."):
            deleted = delete_index()

        if deleted:
            st.success("✅ Index cleared. You can fetch fresh data now.")
        else:
            st.info("Index was already empty or not found.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>Finance Dashboard powered by Endee + OpenAI + Streamlit + yfinance</p>",
    unsafe_allow_html=True
)
