import os


def get_key():
    # 1. local .env file (your computer)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    # 2. environment variable (cloud server)
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()

    # 3. Streamlit secrets (cloud server)
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None