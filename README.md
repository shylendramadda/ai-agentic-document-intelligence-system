# AI Agentic Document Intelligence System

An enterprise-grade document Q&A system built on retrieval-augmented generation (RAG) with safety-first guardrails and lightweight agent orchestration. Designed for the Edureka AI Capstone project.

## Features

- **Multi-format ingestion**: PDF, TXT, CSV, and Excel file support
- **Grounded retrieval**: TF-IDF + cosine similarity for stable, interpretable document matching
- **Safety-first generation**: LLM answers are constrained to retrieved context; includes explicit "DO NOT HALLUCINATE" prompt
- **REST API**: FastAPI backend with `/upload` and `/ask` endpoints
- **User-friendly UI**: Streamlit frontend with document history and expanded source citations
- **Session management**: Track uploaded documents and retrieve sources for every answer

## Architecture

### Data Flow

```
User Document → [Document Processor] → Text Extraction & Chunking
                                              ↓
                                    [Vector Store (TF-IDF)]
                                              ↓
User Question → [Retrieval Agent] → Similarity Search → Top Chunks
                                              ↓
                        [Grounded Context] + LLM Prompt + Safety Guardrail
                                              ↓
                                    Groq API (llama-2-70b-chat)
                                              ↓
                                        Grounded Answer + Sources
```

### Design Rationale

- **TF-IDF Retrieval**: Chosen for stability and simplicity. Avoids dependency friction from embedding models (Keras, TensorFlow) that caused version conflicts in initial prototyping.
- **Lightweight Stack**: FastAPI + Streamlit provide a clear separation of concerns without unnecessary complexity.
- **Groq Integration**: OpenAI-compatible endpoint; API key stored securely in `.env`.
- **Safety Prompt**: The system prompt explicitly includes "DO NOT HALLUCINATE" and ties all responses to retrieved context.

## Installation & Execution Guide

### Prerequisites
- Python 3.11+ (verify with `python --version`)
- A Groq API key (sign up at https://console.groq.com)
- Git (optional, if cloning from repository)

### Step 1: Navigate to Project Directory

```bash
cd /path/to/ai-agentic-document-intelligence
```

If cloning from scratch:
```bash
git clone <repository-url>
cd ai-agentic-document-intelligence
```

### Step 2: Create and Activate Virtual Environment

**macOS / Linux:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

You should see `(.venv)` prefix in your terminal after activation.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Expected output: Successfully installed [list of packages]

### Step 4: Set Up Environment Secrets

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your Groq API key:
```bash
# macOS / Linux:
nano .env

# Windows:
notepad .env
```

Add your credentials:
```ini
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-2-70b-chat
```

**Note**: Never commit `.env` to version control. It's listed in `.gitignore`.

### Step 5: Verify Installation

Test that everything is set up correctly:
```bash
python -m pytest -q
```

Expected output:
```
3 passed in 1.5s
```

### Step 6: Start the Application

Launch the backend and Streamlit frontend together:
```bash
python start_app.py
```

You'll see output similar to:
```
[INFO] Starting FastAPI backend on http://localhost:8000
[INFO] Starting Streamlit frontend on http://localhost:8501
```

### Step 7: Open the Web UI

Open your browser and navigate to:
- **Streamlit App (Main UI)**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs (for developers)
- **Health Check**: http://localhost:8000/health

### Step 8: Upload a Document

1. In the Streamlit app, go to the file uploader
2. Select a document (PDF, TXT, CSV, or Excel)
3. Click **Upload & Index**
4. Wait for "Document ingested successfully" message
5. Check the sidebar to confirm the file appears in "Uploaded files"

### Step 9: Ask a Question

1. In the text area, type your question (e.g., "What is the main topic of this document?")
2. Click **Ask Question**
3. Wait for the spinner to complete
4. Review the answer in the "Answer" box
5. Click "Supporting sources" expanders to see which document chunks were used

### Step 10: Explore Results

- **Answer**: Grounded response based only on retrieved context
- **Metrics**: Shows how many chunks were retrieved and files are indexed
- **Sources**: Click expanders to see the exact text that supports the answer
- **Document History**: View all uploaded files in the left sidebar
- **Clear Session**: Reset and start fresh with new documents

---

## Quick Reference Commands

| Task                   | Command                            |
| ---------------------- | ---------------------------------- |
| Activate environment   | `source .venv/bin/activate`        |
| Deactivate environment | `deactivate`                       |
| Start application      | `python start_app.py`              |
| Run tests              | `pytest -q`                        |
| View API docs          | Visit `http://localhost:8000/docs` |
| Stop backend           | Press `Ctrl+C` in terminal         |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named..."
**Solution**: Ensure virtual environment is activated (see Step 2) and dependencies are installed (Step 3).
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "GROQ_API_KEY not found"
**Solution**: Verify `.env` file exists and contains `GROQ_API_KEY=<your-key>`.
```bash
cat .env  # macOS/Linux
type .env  # Windows
```

### Issue: "Connection refused" when uploading
**Solution**: Ensure the backend is running. Check that `python start_app.py` is still running in your terminal.

### Issue: Slow response or timeout
**Solution**: 
- First question is slower (Groq API warmup)
- Large documents take longer to process
- Try a smaller test document first

### Issue: Port 8501 or 8000 already in use
**Solution**: Either stop other services using those ports or modify `start_app.py` to use different ports.

---

## Testing the API Directly (Optional)

If you prefer to test via command line instead of the UI:

```bash
# Health check
curl http://localhost:8000/health

# Upload a document
curl -X POST -F "file=@/path/to/document.pdf" http://localhost:8000/upload

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

## API Endpoints

### POST `/upload`
Upload and index a document.
- **Request**: Multipart file upload
- **Response**: `{ "message": "Document ingested successfully", "chunks": <number> }`

### POST `/ask`
Ask a question about ingested documents.
- **Request**: `{ "question": "Your question here" }`
- **Response**: 
  ```json
  {
    "answer": "Grounded answer text",
    "sources": [
      { "source": "filename.pdf", "content": "relevant chunk" },
      ...
    ],
    "retrieved_chunks": 3
  }
  ```

### GET `/health`
Health check endpoint.
- **Response**: `{ "status": "ok" }`

## Frontend Usage

1. Upload a document (PDF, TXT, CSV, or Excel)
2. Click **Upload & Index** to process
3. Enter a question in the text area
4. Click **Ask Question**
5. Review the grounded answer and expand sources for details

### Session Features
- **Document history**: All uploaded files shown in the sidebar
- **Clear session**: Reset the document list and start fresh
- **Source citations**: Click to expand and read the exact chunks that support the answer
- **Metrics**: View the number of retrieved chunks and indexed files

## Project Structure

```
.
├── app/
│   ├── backend/
│   │   ├── main.py           # FastAPI server
│   │   └── agent_service.py  # RAG orchestration
│   ├── core/
│   │   ├── config.py         # Settings & secrets
│   │   ├── document_processor.py  # Text extraction & chunking
│   │   └── vector_store.py   # TF-IDF retrieval
│   └── frontend/
│       └── streamlit_app.py  # UI
├── tests/
│   └── test_*.py             # Unit tests
├── data/
│   ├── uploads/              # Temporary uploaded files
│   └── indexes/              # Indexed document data
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── start_app.py              # Launcher script
```

## Testing

Run the test suite:

```bash
pytest -q
```

Expected output:
```
3 passed in 1.5s
```

Tests cover:
- Document ingestion and text extraction
- Vector store retrieval
- Agent orchestration and grounding

## Safety & Guardrails

The system enforces grounded answers through:

1. **Explicit prompt**: The LLM system message includes "DO NOT HALLUCINATE"
2. **Context grounding**: All answers must reference retrieved document chunks
3. **Source tracking**: Every answer includes citations to supporting sources
4. **Fallback behavior**: If no relevant chunks are found, the system reports insufficient context

## Deployment Considerations

- **Environment secrets**: Use `.env` for local development; use managed secrets (e.g., GCP Secret Manager, AWS Secrets Manager) for production
- **API rate limits**: Groq API has usage limits; monitor and scale as needed
- **Storage**: Upload and index directories (`data/uploads`, `data/indexes`) should be on persistent storage in production
- **Concurrency**: FastAPI can handle multiple concurrent requests; scale horizontally as needed
- **Logging**: Extend `agent_service.py` with structured logging for production monitoring

## Capstone Submission Checklist

- [x] Document ingestion (PDF, TXT, CSV, Excel)
- [x] Text extraction and chunking
- [x] Retrieval mechanism (TF-IDF + cosine similarity)
- [x] LLM integration (Groq API)
- [x] RAG answer generation
- [x] REST API endpoints
- [x] Streamlit frontend
- [x] Safety guardrail ("DO NOT HALLUCINATE")
- [x] Unit tests (pytest)
- [x] Environment-based secrets
- [x] Project documentation

## Future Enhancements

- Integrate advanced embeddings (OpenAI, Sentence Transformers) for semantic search
- Add multi-turn conversation history
- Implement document summarization
- Support for more file formats (DOCX, PPT, JSON)
- Fine-tuning the LLM on domain-specific data
- Metrics and analytics dashboard
