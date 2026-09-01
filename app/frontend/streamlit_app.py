import requests
import streamlit as st
from datetime import datetime
from html import escape

API_BASE_URL = "http://localhost:8000"

# Session state initialization
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "latest_response" not in st.session_state:
    st.session_state.latest_response = None

if "pending_toast" not in st.session_state:
    st.session_state.pending_toast = None

if "clear_session_error" not in st.session_state:
    st.session_state.clear_session_error = None

if "clear_session_completed" not in st.session_state:
    st.session_state.clear_session_completed = False

logs_placeholder = None
conversation_placeholder = None


def render_logs():
    if logs_placeholder is None or not st.session_state.get("show_logs", False):
        return
    log_text = "\n".join(st.session_state.logs[-10:])
    if log_text:
        logs_placeholder.text_area("Recent Activity", log_text, height=400, disabled=True)
    else:
        logs_placeholder.caption("No logs yet.")


def render_conversation_history():
    if conversation_placeholder is None:
        return

    with conversation_placeholder.container():
        if st.session_state.conversation_history:
            for index, conversation_index in enumerate(
                range(len(st.session_state.conversation_history) - 1, -1, -1),
                start=1,
            ):
                conversation = st.session_state.conversation_history[conversation_index]
                question_preview = conversation["question"][:45]
                if len(conversation["question"]) > 45:
                    question_preview += "..."
                timestamp = conversation.get("timestamp", "Previous")
                with st.container(border=True):
                    st.markdown(f"**{index}. {timestamp}**  ·  {question_preview}")
                    st.caption(timestamp)
                    st.markdown("**Question**")
                    st.write(conversation["question"])
                    st.markdown("**Answer**")
                    st.write(conversation["answer"])
                    if conversation.get("sources"):
                        st.markdown("**Supporting Sources**")
                        for source in conversation["sources"]:
                            source_name = source.get("source", "Unknown source")
                            st.caption(source_name)
                            st.write(source.get("content", "No source text available."))
                    if st.button("🗑️ Delete", key=f"delete_history_{conversation_index}"):
                        del st.session_state.conversation_history[conversation_index]
                        st.session_state.pending_toast = "Conversation deleted."
                        st.rerun()
        else:
            st.caption("No questions asked yet.")


# Utility function to add timestamped logs
def log_action(action: str, status: str, message: str = ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {status}: {action}"
    if message:
        log_entry += f" - {message}"
    st.session_state.logs.append(log_entry)
    render_logs()


def execute_clear_session():
    try:
        reset_response = requests.post(f"{API_BASE_URL}/reset", timeout=30)
        if not reset_response.ok:
            error_msg = reset_response.json().get("detail", "Backend reset failed")
            raise requests.RequestException(f"HTTP {reset_response.status_code}: {error_msg}")

        st.session_state.uploaded_documents = []
        st.session_state.selected_file = None
        st.session_state.conversation_history = []
        st.session_state.latest_response = None
        st.session_state.logs = []
        log_action("Session Reset", "INFO")
        st.session_state.pending_toast = "Session cleared!"
        st.session_state.clear_session_completed = True
    except requests.RequestException as exc:
        st.session_state.clear_session_error = str(exc)


@st.dialog("Clear Session?")
def confirm_clear_session():
    st.warning("This will delete uploaded documents, indexed content, conversation history, and logs.")
    if st.session_state.get("clear_session_error"):
        st.error(f"Could not clear the backend session: {st.session_state.clear_session_error}")
    st.button("Confirm Clear", use_container_width=True, key="confirm_clear_session_button", on_click=execute_clear_session)

    if st.button("Cancel", use_container_width=True, key="cancel_clear_session_button"):
        st.rerun()

    if st.session_state.clear_session_completed:
        st.session_state.clear_session_completed = False
        st.rerun()

# Page configuration
st.set_page_config(page_title="AI Document Intelligence System", page_icon="📄")
if st.session_state.pending_toast:
    st.toast(st.session_state.pending_toast, icon="✅")
    st.session_state.pending_toast = None

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
        section[data-testid="stSidebar"][aria-expanded="true"],
        section[data-testid="stSidebar"][aria-expanded="true"] > div {
            width: 30rem !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            width: 0 !important;
            min-width: 0 !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] > div {
            width: 0 !important;
            min-width: 0 !important;
            overflow: hidden !important;
        }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0.15rem !important; }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapsedControl"] button {
            margin: 0 !important;
            padding: 0 !important;
            top: 0 !important;
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapsedControl"] button {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
            background-color: #15803d !important;
            color: #166534 !important;
            border: 1px solid #86efac !important;
        }
        [data-testid="stSidebarCollapsedControl"] button svg {
            fill: #166534 !important;
            color: #166534 !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            padding-top: 0.75rem !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
            background-color: #dcfce7 !important;
        }
        section[data-testid="stSidebar"] h2 { text-align: left; margin-top: 0 !important; }
        h1 { font-size: 1.8rem !important; }
        h2, h3 { margin-top: 0.6rem !important; margin-bottom: 0.35rem !important; }
        [data-testid="stCaptionContainer"] { margin-bottom: 0.25rem; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
        hr { margin: 0.5rem 0; }
        .uploaded-files-scroll {
            display: flex;
            gap: 0.45rem;
            overflow-x: auto;
            padding: 0.2rem 0.1rem 0.45rem;
            white-space: nowrap;
        }
        .uploaded-file-chip {
            flex: 0 0 auto;
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 0.25rem 0.55rem;
            color: #334155;
            background: #f8fafc;
            font-size: 0.78rem;
        }
        .uploaded-file-chip:hover {
            color: #15803d !important;
            border-color: #15803d !important;
        }
        div[data-testid="stFileUploader"] label:hover,
        div[data-testid="stFileUploader"] label:hover p,
        div[data-testid="stFileUploader"] label:hover span {
            color: #15803d !important;
        }
        div[data-testid="stFileUploader"] section:hover,
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]:hover,
        div[data-testid="stFileUploader"] button:hover {
            border-color: #15803d !important;
        }
        div[data-testid="stFileUploader"] section:hover,
        div[data-testid="stFileUploader"] section:focus-within,
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]:hover,
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]:focus-within,
        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stFileUploader"] button:focus,
        div[data-testid="stFileUploader"] button:focus-visible,
        div[data-testid="stButton"] button:hover,
        div[data-testid="stButton"] button:focus,
        div[data-testid="stButton"] button:focus-visible {
            border-color: #15803d !important;
            outline-color: #15803d !important;
            box-shadow: 0 0 0 1px #15803d !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:focus,
        div[data-testid="stFormSubmitButton"] button:focus-visible {
            border-color: #15803d !important;
            outline-color: #15803d !important;
            box-shadow: 0 0 0 1px #15803d !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:focus,
        div[data-testid="stFormSubmitButton"] button:focus-visible,
        div[data-testid="stFormSubmitButton"] button:hover p,
        div[data-testid="stFormSubmitButton"] button:focus p {
            color: #15803d !important;
        }
        div[data-testid="stTextArea"] textarea:hover,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextArea"] textarea:focus-visible {
            border-color: #15803d !important;
            outline-color: #15803d !important;
            box-shadow: 0 0 0 1px #15803d !important;
        }
        div[data-testid="stTextArea"] div[data-baseweb="textarea"],
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within > div {
            border-color: #15803d !important;
            outline-color: #15803d !important;
            box-shadow: 0 0 0 1px #15803d !important;
        }
        section[data-testid="stSidebar"] p:hover,
        section[data-testid="stSidebar"] span:hover,
        section[data-testid="stSidebar"] label:hover,
        section[data-testid="stSidebar"] a:hover,
        section[data-testid="stSidebar"] button:hover {
            color: #15803d !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<h1 style="color: #0f766e; margin-bottom: 0.25rem;">AI Agentic Document Intelligence System</h1>',
    unsafe_allow_html=True,
)
st.caption("Upload enterprise documents and ask grounded questions using AI retrieval.")

# Sidebar workflow and history
with st.sidebar:
    st.header("Workflow")
    st.markdown(
        """
        Upload a PDF, TXT, CSV, or Excel file, then ask questions about its content.
        """
    )

    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader("Choose a document", type=["pdf", "txt", "csv", "xlsx", "xls"])
    if uploaded_file is not None:
        st.session_state.selected_file = {
            "name": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "content_type": uploaded_file.type or "application/octet-stream",
        }

    if st.button("Upload & Index", use_container_width=True, key="upload_btn"):
        selected_file = st.session_state.selected_file
        if selected_file is not None:
            file_name = selected_file["name"]
            file_content = selected_file["content"]
            log_action(f"Upload Started: {file_name}", "INFO")
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("📤 Uploading file...")
                progress_bar.progress(25)
                files = {"file": (file_name, file_content, selected_file["content_type"])}
                status_text.text("⏳ Processing and indexing...")
                progress_bar.progress(50)
                response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=120)
                progress_bar.progress(75)

                if response.ok:
                    data = response.json()
                    progress_bar.progress(100)
                    if file_name not in st.session_state.uploaded_documents:
                        st.session_state.uploaded_documents.append(file_name)
                    message = f"{data.get('message', 'Upload successful')} ({data.get('chunks', 0)} chunks)"
                    log_action(f"Upload Complete: {file_name}", "SUCCESS", f"{data.get('chunks', 0)} chunks indexed")
                    st.session_state.pending_toast = message
                    progress_bar.empty()
                    status_text.empty()
                    st.rerun()
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    log_action(f"Upload Failed: {file_name}", "ERROR", error_msg)
                    st.toast(f"✗ Upload failed: {error_msg}", icon="❌")
                    progress_bar.empty()
                    status_text.empty()
            except requests.exceptions.Timeout:
                log_action(f"Upload Timeout: {file_name}", "ERROR", "Request timeout (120s)")
                st.toast("✗ Upload timeout - file may be too large", icon="⏱️")
                progress_bar.empty()
                status_text.empty()
            except Exception as exc:
                log_action(f"Upload Error: {file_name}", "ERROR", str(exc))
                st.toast(f"✗ Error: {str(exc)}", icon="❌")
                progress_bar.empty()
                status_text.empty()
        else:
            st.warning("Please select a file first.")
            log_action("Upload Attempted", "WARNING", "No file selected")

    with st.expander("📁 Uploaded Files", expanded=False):
        if st.session_state.uploaded_documents:
            file_chips = "".join(
                f'<span class="uploaded-file-chip">✓ {escape(file_name)}</span>'
                for file_name in st.session_state.uploaded_documents
            )
            st.markdown(
                f'<div class="uploaded-files-scroll">{file_chips}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No files uploaded yet.")

    with st.expander("💬 Conversation History", expanded=False):
        if st.session_state.conversation_history:
            if st.button("🗑️ Delete all history", key="delete_all_history", use_container_width=True):
                st.session_state.conversation_history = []
                st.session_state.pending_toast = "Conversation history cleared."
                st.rerun()
        conversation_placeholder = st.container(height=240, border=True)
        render_conversation_history()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear Session", use_container_width=True):
            confirm_clear_session()

    with col2:
        if st.button("📋 Show Logs", use_container_width=True):
            st.session_state.show_logs = not st.session_state.get("show_logs", False)

    # Display logs if enabled
    if st.session_state.get("show_logs", False):
        st.subheader("Activity Logs")
        logs_placeholder = st.empty()
        render_logs()

# Main content area
st.divider()

# Question section
with st.container():
    st.subheader("❓ Ask a Question")
    with st.form("question_form", clear_on_submit=True, border=False):
        question_col, submit_col = st.columns([5, 1], vertical_alignment="bottom")
        with question_col:
            question = st.text_area(
                "Enter your question",
                placeholder="Ask anything about the uploaded document...",
                height=120,
            )
        with submit_col:
            submitted = st.form_submit_button("Submit Question", use_container_width=True)

    if submitted:
        if question.strip():
            log_action("Question Submitted", "INFO", question[:50] + "...")
            
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 Retrieving relevant context...")
                progress_bar.progress(33)
                
                response = requests.post(f"{API_BASE_URL}/ask", json={"question": question}, timeout=120)
                
                progress_bar.progress(66)
                
                if response.ok:
                    status_text.text("🤖 Generating answer...")
                    progress_bar.progress(100)
                    
                    payload = response.json()
                    retrieved_chunks = payload.get("retrieved_chunks", 0)
                    question_text = question.strip()
                    history_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": question_text,
                        "answer": payload.get("answer", "No answer generated."),
                        "sources": payload.get("sources", []),
                    }
                    st.session_state.conversation_history = [
                        entry
                        for entry in st.session_state.conversation_history
                        if entry.get("question", "").casefold().strip() != question_text.casefold()
                    ]
                    st.session_state.conversation_history.append(history_entry)
                    log_action("Answer Generated", "SUCCESS", f"{retrieved_chunks} chunks retrieved")
                    st.session_state.pending_toast = "Answer generated successfully!"
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    answer = payload.get("answer", "No answer generated.").strip()
                    sources = payload.get("sources", [])
                    st.session_state.latest_response = {
                        "question": question.strip(),
                        "answer": answer,
                        "sources": sources,
                        "retrieved_chunks": retrieved_chunks,
                    }
                    st.rerun()
                        
                else:
                    progress_bar.progress(100)
                    error_msg = response.json().get('detail', 'Unknown error')
                    log_action("Question Failed", "ERROR", f"HTTP {response.status_code}: {error_msg}")
                    st.toast(f"✗ Query failed: {error_msg}", icon="❌")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
            except requests.exceptions.Timeout:
                log_action("Question Timeout", "ERROR", "Request timeout (120s)")
                st.toast("✗ Request timeout - try a simpler question", icon="⏱️")
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                log_action("Question Error", "ERROR", str(e))
                st.toast(f"✗ Error: {str(e)}", icon="❌")
                progress_bar.empty()
                status_text.empty()
        else:
            st.warning("Please enter a question first.")
            log_action("Question Attempted", "WARNING", "Empty question")

if st.session_state.latest_response:
    latest_response = st.session_state.latest_response
    answer = latest_response["answer"]
    sources = latest_response["sources"]
    retrieved_chunks = latest_response["retrieved_chunks"]

    st.divider()
    st.subheader("💡 Answer")
    st.caption("Question asked")
    st.markdown(f"> {latest_response['question']}")
    st.success(answer)

    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("Relevant chunks", retrieved_chunks)
    with summary_col2:
        source_count = len({item.get("source", "Unknown source") for item in sources})
        st.metric("Source files", source_count)
    with summary_col3:
        st.metric("Indexed files", len(st.session_state.uploaded_documents))

    if sources:
        st.subheader("📚 Supporting Sources")
        st.caption("Expand a source to review the document text used for this answer.")
        for idx, item in enumerate(sources, start=1):
            source_name = item.get("source", "Unknown source")
            content = item.get("content", "").strip()
            with st.expander(f"Source {idx}  ·  {source_name}", expanded=idx == 1):
                st.caption("Retrieved document chunk")
                st.write(content or "No source text available.")
    else:
        st.warning("No matching document content was found for this question.")

