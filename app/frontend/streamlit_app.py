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
                with st.expander(f"{index}. {timestamp}  ·  {question_preview}"):
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

# Page configuration
st.set_page_config(page_title="AI Document Intelligence System", page_icon="📄")
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
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

    with st.expander("📁 Uploaded Files", expanded=True):
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

    st.subheader("💬 Conversation History")
    if st.button(
        "🗑️ Delete all history",
        key="delete_all_history",
        use_container_width=True,
        disabled=not st.session_state.conversation_history,
    ):
        st.session_state.conversation_history = []
        st.rerun()
    conversation_placeholder = st.container(height=240, border=True)
    render_conversation_history()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear Session", use_container_width=True):
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
                st.toast("Session cleared!", icon="✅")
                st.rerun()
            except requests.RequestException as exc:
                log_action("Session Reset Failed", "ERROR", str(exc))
                st.toast("✗ Could not clear the backend session", icon="❌")

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

upload_section, question_section = st.columns([1, 1], gap="medium")

# Upload section
with upload_section:
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
            
            # Progress bar during upload
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("📤 Uploading file...")
                progress_bar.progress(25)
                
                files = {
                    "file": (file_name, file_content, selected_file["content_type"])
                }
                
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
                    st.toast(f"✓ {message}", icon="✅")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    st.rerun()
                else:
                    progress_bar.progress(100)
                    error_msg = response.json().get('detail', 'Unknown error')
                    log_action(f"Upload Failed: {file_name}", "ERROR", error_msg)
                    st.toast(f"✗ Upload failed: {error_msg}", icon="❌")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
            except requests.exceptions.Timeout:
                log_action(f"Upload Timeout: {file_name}", "ERROR", "Request timeout (120s)")
                st.toast("✗ Upload timeout - file may be too large", icon="⏱️")
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                log_action(f"Upload Error: {file_name}", "ERROR", str(e))
                st.toast(f"✗ Error: {str(e)}", icon="❌")
                progress_bar.empty()
                status_text.empty()
        else:
            st.warning("Please select a file first.")
            log_action("Upload Attempted", "WARNING", "No file selected")

# Question section
with question_section:
    st.subheader("❓ Ask a Question")
    with st.form("question_form", clear_on_submit=True, border=False):
        question = st.text_input("Enter your question", placeholder="Ask anything about the uploaded document...")
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
                    st.toast("✓ Answer generated successfully!", icon="✅")
                    
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

