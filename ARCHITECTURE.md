# Architecture & Design Document

## System Overview

The AI Agentic Document Intelligence system is a modular, three-tier architecture designed to ingest, retrieve, and reason over enterprise documents using RAG and LLM-based orchestration.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  Streamlit UI (frontend/streamlit_app.py)                       │
│  - File upload widget                                           │
│  - Question input & session management                          │
│  - Answer display & source expansion                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP (requests)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  FastAPI Server (backend/main.py)                               │
│  ├─ POST /upload → Document ingestion                           │
│  ├─ POST /ask → Question answering                              │
│  └─ GET /health → Service status                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                         │
│  Agent Service (backend/agent_service.py)                       │
│  ├─ ingest_file() → Document processing                         │
│  ├─ answer_question() → RAG pipeline                            │
│  ├─ _grounded_context() → Retrieval + grounding                 │
│  └─ _generate_with_groq() → LLM inference                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌───────────┐ ┌─────────────┐
│   Document   │ │ TF-IDF    │ │ LLM Client  │
│   Processor  │ │ Vector    │ │ (Groq API)  │
│   (core)     │ │ Store     │ │             │
│              │ │ (core)    │ │             │
└──────────────┘ └───────────┘ └─────────────┘
```

## Component Details

### 1. Document Processor (`app/core/document_processor.py`)

**Purpose**: Extract and normalize text from multiple file formats.

**Key Functions**:
- `extract_document_text(file_path)` — Detect file type and extract text
- `read_pdf_file(file_path)` — PDF text extraction using PyPDF2
- `read_csv_file(file_path)` — CSV parsing with pandas
- `read_excel_file(file_path)` — Excel parsing with openpyxl
- `chunk_text(text, chunk_size=1000, overlap=100)` — Sliding window chunking
- `build_chunks_from_file(file_path)` — End-to-end file→chunks pipeline

**Chunking Strategy**:
- **Size**: 1000 characters per chunk
- **Overlap**: 100 characters to preserve context across boundaries
- **Rationale**: Balances retrieval granularity with context preservation

**Supported Formats**:
- PDF (via PyPDF2)
- Plain text (.txt)
- CSV (via pandas)
- Excel (.xlsx, .xls via openpyxl)

---

### 2. Vector Store (`app/core/vector_store.py`)

**Purpose**: Store and retrieve document chunks using similarity search.

**Architecture**: TF-IDF + Cosine Similarity

**Key Functions**:
- `add_documents(documents: list, source: str)` — Index new chunks
- `query(query_text: str, top_k: int = 3)` — Retrieve top-k similar chunks
- `reset()` — Clear the index

**Design Rationale** (Why TF-IDF, not embeddings?):
1. **Stability**: Avoids heavy dependencies (Keras, TensorFlow) that caused version conflicts
2. **Interpretability**: TF-IDF scores are directly understandable; no "black box" embeddings
3. **Performance**: Fast retrieval on small-to-medium document collections
4. **Simplicity**: No need for a separate embedding model or API
5. **Reliability**: Statistical approach proven in information retrieval

**Limitations**:
- Lexical match only (does not capture semantic similarity well)
- Scales poorly with very large collections (millions of documents)
- Requires careful stemming/normalization for consistent results

**Future Upgrade Path**: Replace with Chroma + Sentence Transformers for semantic embeddings.

---

### 3. Agent Service (`app/backend/agent_service.py`)

**Purpose**: Orchestrate the RAG pipeline and LLM reasoning.

**Key Functions**:

#### `ingest_file(file_path: str) → dict`
1. Extract text from file using document processor
2. Chunk the text into manageable pieces
3. Add chunks to the vector store with source metadata
4. Return chunk count and status

#### `answer_question(question: str) → dict`
1. Retrieve grounded context using `_grounded_context()`
2. Generate answer using `_generate_with_groq()`
3. Assemble response with answer, sources, and metadata
4. Return to API layer

#### `_grounded_context(question: str, top_k: int = 3) → (context_text, sources)`
1. Query the vector store for top-k similar chunks
2. Build a context string from retrieved chunks
3. Include source metadata (filename, chunk index)
4. Return context and source list for grounding

#### `_generate_with_groq(question: str, context: str) → str`
1. Construct a safety-enforced system prompt:
   ```
   You are a helpful assistant answering questions grounded in provided context.
   DO NOT HALLUCINATE. Only use the context provided.
   If the context does not contain the answer, say "I cannot answer this question based on the provided context."
   ```
2. Build messages list: [system_prompt, user_question_with_context]
3. Call Groq API via OpenAI-compatible endpoint
4. Return the assistant's response

**Safety Mechanism**:
- The prompt explicitly includes "DO NOT HALLUCINATE"
- All questions are prefixed with retrieved context
- If no relevant context exists, the LLM is instructed to report insufficient context
- Fallback: If Groq API fails, return a grounded summary of retrieved chunks

---

### 4. FastAPI Server (`app/backend/main.py`)

**Purpose**: Expose HTTP endpoints for upload and query.

**Endpoints**:

| Method | Path      | Request                  | Response                                                        |
| ------ | --------- | ------------------------ | --------------------------------------------------------------- |
| GET    | `/health` | None                     | `{ "status": "ok" }`                                            |
| POST   | `/upload` | Multipart file           | `{ "message": "...", "chunks": N }`                             |
| POST   | `/ask`    | `{ "question": string }` | `{ "answer": string, "sources": [...], "retrieved_chunks": N }` |

**Error Handling**:
- 400: Invalid input (e.g., unsupported file type)
- 500: Server error (e.g., Groq API unavailable)

---

### 5. Streamlit Frontend (`app/frontend/streamlit_app.py`)

**Purpose**: Provide a user-friendly interface for document upload and Q&A.

**Key Features**:
- **File Uploader**: Drag-drop interface for PDF, TXT, CSV, Excel
- **Upload & Index**: Synchronous upload with spinner feedback
- **Question Input**: Text area for natural-language questions
- **Document History**: Sidebar showing all uploaded files
- **Session Management**: Clear session button to reset state
- **Answer Display**: Info box with the grounded response
- **Metrics**: Count of retrieved chunks and indexed files
- **Source Expansion**: Expandable sections showing retrieved chunks with source attribution

---

## Data Flow: Complete Example

### Scenario: Upload a PDF and ask a question

```
1. User uploads "company_policy.pdf" via Streamlit
   └─> POST /upload → backend/main.py
       └─> AgentService.ingest_file("company_policy.pdf")
           ├─> DocumentProcessor.extract_document_text()
           │   └─> PyPDF2 extracts text from PDF
           ├─> DocumentProcessor.chunk_text()
           │   └─> [chunk_1, chunk_2, ..., chunk_n]
           └─> VectorStore.add_documents([chunks], source="company_policy.pdf")
               └─> Compute TF-IDF scores and store metadata

2. User asks: "What is the overtime policy?"
   └─> POST /ask → backend/main.py
       └─> AgentService.answer_question("What is the overtime policy?")
           ├─> _grounded_context("What is the overtime policy?", top_k=3)
           │   └─> VectorStore.query("overtime policy", top_k=3)
           │       └─> Cosine similarity matching
           │           └─> Returns [source_chunk_1, source_chunk_2, source_chunk_3]
           │   └─> Format context: "Context: [chunk_1] ... [chunk_3]"
           │
           └─> _generate_with_groq("What is the overtime policy?", context)
               └─> System prompt: "DO NOT HALLUCINATE. Use only provided context."
               └─> API call: https://api.groq.com/openai/v1/chat/completions
               └─> Response: "Based on the company policy, overtime is..."
           
           └─> Return {
                 "answer": "Based on the company policy...",
                 "sources": [
                   {"source": "company_policy.pdf", "content": "[chunk_1]"},
                   {"source": "company_policy.pdf", "content": "[chunk_2]"},
                   ...
                 ],
                 "retrieved_chunks": 3
               }

3. Streamlit renders:
   ├─ Answer box: "Based on the company policy..."
   ├─ Metrics: "Retrieved chunks: 3, Files indexed: 1"
   └─ Expandable sources: [Source 1: company_policy.pdf, ...]
```

---

## Configuration (`app/core/config.py`)

**Purpose**: Centralized settings management.

**Key Settings**:
- `app_name`: Application identifier
- `upload_dir`: Directory for temporary uploads (default: `data/uploads/`)
- `index_dir`: Directory for vector store index (default: `data/indexes/`)
- `max_upload_size_mb`: File size limit (default: 50 MB)
- `allowed_extensions`: Supported file types (`.pdf`, `.txt`, `.csv`, `.xlsx`, `.xls`)
- `groq_api_key`: Groq API key (from `.env`)
- `groq_model`: LLM model name (default: `llama-2-70b-chat`)

**Environment-Based Secrets**:
- Reads from `.env` file using `pydantic-settings`
- Never hardcodes credentials
- Falls back to defaults for non-sensitive settings

---

## Testing Strategy (`tests/`)

**Test Coverage**:

| Test                         | Purpose                              |
| ---------------------------- | ------------------------------------ |
| `test_document_processor.py` | Verify text extraction and chunking  |
| `test_vector_store.py`       | Verify TF-IDF indexing and retrieval |
| `test_agent_service.py`      | Verify end-to-end RAG pipeline       |

**Running Tests**:
```bash
pytest -q
# Expected: 3 passed in ~1.5s
```

---

## Deployment Considerations

### Local Development
- FastAPI backend runs on `http://localhost:8000`
- Streamlit frontend runs on `http://localhost:8501`
- Both share access to local `data/` directory

### Production Deployment

1. **Secrets Management**:
   - Use managed services: GCP Secret Manager, AWS Secrets Manager
   - Avoid `.env` files in production
   - Rotate API keys regularly

2. **Storage**:
   - Move `data/uploads/` and `data/indexes/` to persistent storage (e.g., GCS, S3)
   - Consider object lifecycle policies for cleanup

3. **API Rate Limiting**:
   - Groq API has usage limits; monitor and implement backoff
   - Cache common queries to reduce API calls

4. **Logging & Monitoring**:
   - Use structured logging (e.g., Python logging + JSON formatters)
   - Monitor API latency, error rates, and Groq API usage
   - Set up alerts for failed uploads or retrieval timeouts

5. **Horizontal Scaling**:
   - FastAPI is stateless; scale horizontally behind a load balancer
   - Store index in shared persistent storage (not local disk)
   - Use a message queue (e.g., Celery, Cloud Tasks) for async ingestion

6. **Security**:
   - Enable HTTPS (TLS/SSL)
   - Implement authentication (JWT, OAuth2)
   - Use API rate limiting to prevent abuse
   - Sanitize user inputs to prevent prompt injection

---

## Future Enhancements

### Short Term
- **Multi-turn conversation**: Store chat history; maintain context across questions
- **Query rephrasing**: Use LLM to rephrase questions for better retrieval
- **Chunk re-ranking**: Implement a second-pass ranker (e.g., cross-encoder) for better relevance

### Medium Term
- **Semantic embeddings**: Integrate Sentence Transformers or OpenAI embeddings
- **Hybrid search**: Combine TF-IDF with semantic similarity
- **Document summarization**: Automatically generate summaries of large documents
- **Fine-tuning**: Fine-tune Llama 2 on domain-specific Q&A pairs

### Long Term
- **Knowledge graphs**: Extract entities and relationships from documents
- **Multi-modal support**: Handle images, tables, and structured data
- **Fact verification**: Verify LLM outputs against retrieved context with confidence scores
- **Distributed RAG**: Federated retrieval across multiple document sources
