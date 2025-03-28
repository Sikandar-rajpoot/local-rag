import streamlit as st
import requests
import json
from streamlit.components.v1 import html
import os
import tempfile

# API base URL
BASE_URL = "http://localhost:8000/rag"

# Streamlit app
st.title("RAG System Dashboard")

# Tabs with improved styling
tab1, tab2, tab3 = st.tabs(["File RAG", "File Automation", "History"])

# Tab 1: Query RAG
with tab1:
    with st.container():
        st.header("File RAG System")
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("Enter your query", key="query")
        with col2:
            submit_query = st.button("Submit Query", key="submit_query", 
                                   help="Click to submit your query",
                                   use_container_width=True)
            st.markdown("""
                <style>
                    [data-testid="stButton"] {
                        margin-top: 28px;
                    }
                </style>
                """, unsafe_allow_html=True)
        
        col_paths, col_upload = st.columns(2)
        with col_paths:
            file_paths = st.text_area("Enter file paths (one per line)", key="file_paths")
        with col_upload:
            uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True, type=["txt", "pdf", "docx"])
        
        if submit_query and query:
            file_paths_list = [fp.strip() for fp in file_paths.split("\n") if fp.strip()]
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                        tmp.write(uploaded_file.read())
                        file_paths_list.append(tmp.name)
            try:
                response = requests.post(
                    f"{BASE_URL}/query",
                    json={"query": query, "file_paths": file_paths_list}
                )
                response.raise_for_status()
                result = response.json()
                st.subheader("Response:")
                # Inline styling for response-box, theme-aware colors
                html_response = (
                    f"<div style='background: linear-gradient(135deg, #d4fce3 0%, #c8e6c9 100%) "
                    f"{'background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"padding: 1.5rem; border-radius: 10px; border: 1px solid #a5d6a7 "
                    f"{'border: 1px solid #4caf50' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"color: #1b5e20 {'color: #e8f5e9' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"font-size: 1.1rem; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.1); "
                    f"margin-top: 1rem; margin-bottom: 1rem; max-height: 600px; "
                    f"font-family: Poppins, sans-serif;'>"
                    f"{result['response']}</div>"
                )
                html(html_response, height=600, scrolling=True)

                # Collapsible Context with Inline Styling
                with st.expander("Context", expanded=True):
                    context_html = (
                        f"<div style='background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%) "
                        f"{'background: linear-gradient(135deg, #006064 0%, #00838f 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"padding: 1.5rem; border-radius: 10px; border: 1px solid #80deea "
                        f"{'border: 1px solid #26c6da' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"color: #006064 {'color: #e0f7fa' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"font-size: 1rem; box-shadow: 0 4px 12px rgba(0, 96, 100, 0.1); "
                        f"margin-top: 1rem; max-height: 400px; "
                        f"font-family: Poppins, sans-serif;'>"
                    )
                    for i, ctx in enumerate(result["context"], 1):
                        context_html += (
                            f"<p style='margin: 5px 0; padding: 8px; background-color: rgba(255, 255, 255, 0.3); "
                            f"border-radius: 5px;'><strong>Chunk {i}:</strong> {ctx.replace('\n', '<br>')}</p>"
                        )
                    context_html += "</div>"
                    html(context_html, height=400)

                # Collapsible Metadata with Inline Styling
                with st.expander("Metadata", expanded=True):
                    meta_html = (
                        f"<div style='background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%) "
                        f"{'background: linear-gradient(135deg, #311b92 0%, #5e35b1 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"padding: 1.5rem; border-radius: 10px; border: 1px solid #b39ddb "
                        f"{'border: 1px solid #9575cd' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"color: #311b92 {'color: #ede7f6' if st.get_option('theme.base') == 'dark' else ''}; "
                        f"font-size: 0.95rem; box-shadow: 0 4px 12px rgba(49, 27, 146, 0.1); "
                        f"margin-top: 1rem; max-height: 250px; overflow-y: auto; "
                        f"font-family: Poppins, sans-serif;'>"
                        f"<table style='width: 100%; border-collapse: collapse;'>"
                        f"<tr style='background-color: rgba(255, 255, 255, 0.4);'>"
                        f"<th style='padding: 8px; border: 1px solid #fff;'>File</th>"
                        f"<th style='padding: 8px; border: 1px solid #fff;'>Source</th>"
                        f"</tr>"
                    )
                    for meta in result["metadata"]:
                        meta_html += (
                            f"<tr style='background-color: rgba(255, 255, 255, 0.3);'>"
                            f"<td style='padding: 8px; border: 1px solid #fff;'>{meta['file']}</td>"
                            f"<td style='padding: 8px; border: 1px solid #fff;'>{meta['source']}</td>"
                            f"</tr>"
                        )
                    meta_html += "</table></div>"
                    html(meta_html, height=250)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")
            finally:
                for fp in file_paths_list:
                    if fp.startswith(tempfile.gettempdir()) and os.path.exists(fp):
                        os.remove(fp)
        elif submit_query:
            st.warning("Please enter a query")

# Tab 2: File Automation
with tab2:
    with st.container():
        st.header("File Automation")
        col1, col2 = st.columns([3, 1])
        with col1:
            prompt = st.text_input("Enter automation prompt", key="prompt")
        with col2:
            execute_automation = st.button("Execute", key="execute_automation",
                                           help="Click to execute the automation prompt",
                                           use_container_width=True)
            st.markdown("""
                <style>
                    [data-testid="stButton"] {
                        margin-top: 28px;
                    }
                </style>
                """, unsafe_allow_html=True)
        
        st.subheader("Search Files")
        col_dir, col_pattern = st.columns(2)
        with col_dir:
            search_dir = st.text_input("Directory to search", key="search_dir", value="D:/temp")
        with col_pattern:
            search_pattern = st.text_input("Search pattern (e.g., *.txt)", key="search_pattern", value="*")
        search_button = st.button("Search", key="search_button",
                                  help="Click to search for files",
                                  use_container_width=True)
        st.markdown("""
            <style>
                [data-testid="stButton"] {
                    margin-top: 28px;
                }
            </style>
            """, unsafe_allow_html=True)
        
        if search_button:
            search_prompt = f"Search for {search_pattern} in {search_dir}"
            try:
                response = requests.post(f"{BASE_URL}/automate", json={"prompt": search_prompt})
                response.raise_for_status()
                result = response.json()
                result_html = (
                    f"<div style='background: linear-gradient(135deg, #d4fce3 0%, #c8e6c9 100%) "
                    f"{'background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"padding: 1.5rem; border-radius: 10px; border: 1px solid #a5d6a7 "
                    f"{'border: 1px solid #4caf50' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"color: #1b5e20 {'color: #e8f5e9' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"font-size: 1.1rem; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.1); "
                    f"margin-top: 1rem; margin-bottom: 1rem; font-family: Poppins, sans-serif;'>"
                    f"Search Result: {result['result']}</div>"
                )
                html(result_html, height=200)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")

        if execute_automation and prompt:
            try:
                response = requests.post(f"{BASE_URL}/automate", json={"prompt": prompt})
                response.raise_for_status()
                result = response.json()
                st.subheader("Result:")
                result_html = (
                    f"<div style='background: linear-gradient(135deg, #d4fce3 0%, #c8e6c9 100%) "
                    f"{'background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"padding: 1.5rem; border-radius: 10px; border: 1px solid #a5d6a7 "
                    f"{'border: 1px solid #4caf50' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"color: #1b5e20 {'color: #e8f5e9' if st.get_option('theme.base') == 'dark' else ''}; "
                    f"font-size: 1.1rem; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.1); "
                    f"margin-top: 1rem; margin-bottom: 1rem; font-family: Poppins, sans-serif;'>"
                    f"{result['result']}</div>"
                )
                html(result_html, height=200)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")
        elif execute_automation:
            st.warning("Please enter an automation prompt")

# Tab 3: History
with tab3:
    with st.container():
        st.header("Interaction History")
        col_filter, col_refresh = st.columns([2, 1])
        with col_filter:
            filter_type = st.selectbox("Filter by Type", ["All", "Query", "Automation"], key="filter_type")
        with col_refresh:
            refresh_history = st.button("Refresh History", key="refresh_history",
                                        help="Click to refresh the history",
                                        use_container_width=True)
            st.markdown("""
                <style>
                    [data-testid="stButton"] {
                        margin-top: 28px;
                    }
                </style>
                """, unsafe_allow_html=True)
        
        if refresh_history:
            try:
                response = requests.get(f"{BASE_URL}/history")
                response.raise_for_status()
                history = response.json()
                if history:
                    if filter_type != "All":
                        history = [entry for entry in history if entry["type"].lower() == filter_type.lower()]
                    for entry in history:
                        with st.expander(f"{entry['type'].capitalize()} - {entry['timestamp']}", expanded=False):
                            st.markdown(f"**Query/Prompt:** {entry['query']}")
                            st.markdown(f"**File Paths:** {entry['file_paths']}")
                            # Process and render HTML response with inline styling
                            response_html = (
                                f"<div style='background: linear-gradient(135deg, #d4fce3 0%, #c8e6c9 100%) "
                                f"{'background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)' if st.get_option('theme.base') == 'dark' else ''}; "
                                f"padding: 1.5rem; border-radius: 10px; border: 1px solid #a5d6a7 "
                                f"{'border: 1px solid #4caf50' if st.get_option('theme.base') == 'dark' else ''}; "
                                f"color: #1b5e20 {'color: #e8f5e9' if st.get_option('theme.base') == 'dark' else ''}; "
                                f"font-size: 1.1rem; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.1); "
                                f"margin-top: 1rem; margin-bottom: 1rem; min-height: 100px;"
                                f"font-family: Poppins, sans-serif;'>"
                                f"{entry['response']}</div>"
                            )
                            st.markdown("**Response:**")
                            html(response_html, height=400, scrolling=True)
                            if entry["details"]:
                                st.markdown(f"**Details:** {entry['details']}")
                else:
                    st.info("No history available")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching history: {str(e)}")

# Sidebar Instructions
st.sidebar.header("Instructions")
st.sidebar.markdown("""
- **File RAG**: Query with file paths or uploads. No input uses vector DB.
- **File Automation**: Examples:
  - "Create files /path/test1.txt and /path/test2.txt with content Hello"
  - "Write an article to /path/article.md from vector database"
  - "Write an article to /path/article.html about AI"
  - "Search for *.txt in /path/dir"
  - "Delete all files from /path/dir"
- **History**: Expand entries for details.
""", unsafe_allow_html=True)