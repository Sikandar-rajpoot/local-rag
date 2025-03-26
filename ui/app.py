import streamlit as st
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/rag"

# Streamlit app
st.title("RAG System with File Management")

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Query RAG", "File Automation", "History"])

# Tab 1: Query RAG
with tab1:
    st.header("Query RAG System")
    query = st.text_input("Enter your query", key="query")
    file_path = st.text_input("Enter file path", key="file_path")
    if st.button("Submit Query"):
        if query and file_path:
            try:
                response = requests.post(
                    f"{BASE_URL}/query",
                    json={"query": query, "file_path": file_path}
                )
                response.raise_for_status()
                result = response.json()
                st.success("Response:")
                st.write(result["response"])
                st.subheader("Context:")
                st.write(result["context"])
                st.subheader("Metadata:")
                st.write(result["metadata"])
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter both query and file path")

# Tab 2: File Automation
with tab2:
    st.header("File Automation")
    prompt = st.text_area("Enter automation prompt", key="prompt")
    if st.button("Execute Automation"):
        if prompt:
            try:
                response = requests.post(
                    f"{BASE_URL}/automate",
                    json={"prompt": prompt}
                )
                response.raise_for_status()
                result = response.json()
                st.success(f"Result: {result['result']}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter an automation prompt")

# Tab 3: History
with tab3:
    st.header("Interaction History")
    if st.button("Refresh History"):
        try:
            response = requests.get(f"{BASE_URL}/history")
            response.raise_for_status()
            history = response.json()
            if history:
                st.table(history)
            else:
                st.info("No history available")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching history: {str(e)}")

# Instructions
st.sidebar.header("Instructions")
st.sidebar.write("""
- **Query RAG**: Ask questions about a file (e.g., "What is the third planet?" with path "documents/knowledge.txt").
- **File Automation**: Use prompts like "Create a file /path/test.txt with content Hello" or "Move /path/test.txt to /path/archive".
- **History**: View past queries and automation tasks. 'Type' column shows 'query' or 'automation'.
""")