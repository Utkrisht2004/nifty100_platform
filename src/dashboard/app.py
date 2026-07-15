import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Welcome to Nifty 100 Analytics 📈")
st.markdown("""
### The intelligent quantitative engine.
Please select a module from the sidebar to begin analyzing fundamental data, peer percentiles, and market valuations.
""")
