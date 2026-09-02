# AI Agentic Document Intelligence System

GitHub repository: https://github.com/shylendramadda/ai-agentic-document-intelligence-system

An enterprise-grade document Q&A system built on retrieval-augmented generation (RAG) with safety-first guardrails and lightweight agent orchestration. Designed for the Edureka AI Capstone project.

## Screenshots

### Dashboard

![AI Agentic Document Intelligence dashboard](1.%20Dashboard.jpeg)

### Answer and Supporting Sources

![Grounded answer with supporting sources](2.%20Answer.jpeg)

## Features

- **Multi-format ingestion**: PDF, TXT, CSV, and Excel file support (`.xls` and `.xlsx`)
- **Grounded retrieval**: TF-IDF + cosine similarity for stable, interpretable document matching
- **Safety-first generation**: LLM answers are constrained to retrieved context; includes explicit "DO NOT HALLUCINATE" prompt
- **REST API**: FastAPI backend with `/upload`, `/ask`, `/reset`, and `/health` endpoints
- **User-friendly UI**: Streamlit frontend with document history and expanded source citations
- **Session management**: Track uploaded documents, conversation history, and sources for every answer
- **Persistent index**: Save indexed chunks to `data/indexes/documents.json` across restarts

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
                                    Groq API (configured by `GROQ_MODEL`)
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
- Tesseract OCR for scanned PDFs:
  - **macOS**: `brew install tesseract`
  - **Linux (Debian/Ubuntu)**: `sudo apt-get install tesseract-ocr`
  - **Windows**: Install from https://github.com/UB-Mannheim/tesseract/wiki, then add the install folder (e.g. `C:\Program Files\Tesseract-OCR`) to your `PATH`
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
GROQ_MODEL=openai/gpt-oss-120b
```

The `requirements.txt` file includes `xlrd` for reading legacy `.xls` files and `openpyxl` for `.xlsx` files.

**Note**: Never commit `.env` to version control. It's listed in `.gitignore`.

### Step 5: Verify Installation

Test that everything is set up correctly:
```bash
python -m pytest -q
```

Expected output:
```
26 passed
```

### Step 6: Start the Application

> **Important:** Run this with the **same Python that has the dependencies installed** — i.e. the activated virtual environment from Step 2. `start_app.py` launches the backend and frontend using `sys.executable`, so if you run it with a different (system) Python that lacks `uvicorn`/`streamlit`, the backend crashes and the browser shows `ERR_CONNECTION_REFUSED` on port 8501.

**With the virtual environment activated (recommended):**
```bash
python start_app.py
```

**Or call the venv's Python directly (no activation needed):**

macOS / Linux:
```bash
.venv/bin/python start_app.py
```

Windows (PowerShell / Command Prompt):
```powershell
.venv\Scripts\python.exe start_app.py
```

You'll see output similar to:
```
Backend: http://127.0.0.1:8000
Frontend: http://127.0.0.1:8501
```

> **First-run note:** On the very first launch, Streamlit may prompt for an email on the terminal (`Email:`). Press **Enter** to skip it. To avoid this prompt entirely (useful for non-interactive/background launches), create an empty credentials file first:
>
> macOS / Linux:
> ```bash
> mkdir -p ~/.streamlit && printf '[general]\nemail = ""\n' > ~/.streamlit/credentials.toml
> ```
> Windows (PowerShell):
> ```powershell
> mkdir "$env:USERPROFILE\.streamlit" -Force; Set-Content "$env:USERPROFILE\.streamlit\credentials.toml" "[general]`nemail = `"`""
> ```

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

1. In the question input, type your question (e.g., "What is the main topic of this document?")
2. Click **Submit Question**
3. Wait for the spinner to complete
4. Review the answer in the "Answer" box
5. Click "Supporting sources" expanders to see which document chunks were used

### Step 10: Explore Results

- **Answer**: Grounded response based only on retrieved context
- **Metrics**: Shows how many chunks were retrieved and files are indexed
- **Sources**: Click expanders to see the exact text that supports the answer
- **Document History**: View all uploaded files in the left sidebar
- **Clear Session**: Reset the document list, conversation history, and backend index

---

## Quick Reference Commands

| Task                          | Command                                                        |
| ----------------------------- | -------------------------------------------------------------- |
| Activate environment (macOS/Linux) | `source .venv/bin/activate`                               |
| Activate environment (Windows PS)  | `.venv\Scripts\Activate.ps1`                             |
| Deactivate environment        | `deactivate`                                                   |
| Start application             | `python start_app.py`                                          |
| Start without activating (macOS/Linux) | `.venv/bin/python start_app.py`                       |
| Start without activating (Windows)     | `.venv\Scripts\python.exe start_app.py`               |
| Run tests                     | `pytest -q`                                                    |
| View API docs                 | Visit `http://localhost:8000/docs`                             |
| Stop backend                  | Press `Ctrl+C` in terminal                                     |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named..." / browser shows `ERR_CONNECTION_REFUSED`
**Cause**: You're running `start_app.py` with a Python that doesn't have the dependencies (commonly the system Python instead of the virtual environment). The backend then crashes and the frontend never starts.
**Solution**: Activate the virtual environment first (see Step 2), or run `start_app.py` with the venv's Python directly.
```bash
# macOS / Linux
source .venv/bin/activate && pip install -r requirements.txt
python start_app.py
# ...or, without activating:
.venv/bin/python start_app.py
```
```powershell
# Windows
.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
python start_app.py
# ...or, without activating:
.venv\Scripts\python.exe start_app.py
```

### Issue: Frontend exits immediately / stuck on Streamlit `Email:` prompt
**Cause**: On first run Streamlit asks for an email on the terminal; in a non-interactive launch this makes the frontend exit.
**Solution**: Press **Enter** at the prompt, or pre-create an empty credentials file (see the First-run note in Step 6).

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

### POST `/reset`
Reset the in-memory and persisted document index.
- **Response**: `{ "status": "ok", "message": "Document index reset successfully." }`

### GET `/health`
Health check endpoint.
- **Response**: `{ "status": "ok" }`

## Frontend Usage

1. Upload a document (PDF, TXT, CSV, or Excel)
2. Click **Upload & Index** to process
3. Enter a question in the compact question input
4. Click **Submit Question**
5. Review the grounded answer and expand sources for details

### Session Features
- **Document history**: All uploaded files shown in the sidebar
- **Clear session**: Reset the document list, conversation history, and backend index
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
26 passed
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
- Add persistent conversation history across application restarts
- Implement document summarization
- Support for more file formats (DOCX, PPT, JSON)
- Fine-tuning the LLM on domain-specific data
- Metrics and analytics dashboard
