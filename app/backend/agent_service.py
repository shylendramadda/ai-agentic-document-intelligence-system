from typing import Any, Dict, List

import requests

from app.core.config import settings
from app.core.document_processor import build_chunks_from_file
from app.core.vector_store import VectorKnowledgeStore


class DocumentAgent:
    def __init__(self, vector_store: VectorKnowledgeStore | None = None):
        self.vector_store = vector_store or VectorKnowledgeStore()

    def ingest_file(self, file_path: str, file_name: str) -> List[str]:
        chunks = build_chunks_from_file(file_path)
        metadata = [{"source": file_name, "chunk_index": index} for index in range(len(chunks))]
        self.vector_store.add_documents(chunks, metadata)
        return chunks

    def reset(self) -> None:
        self.vector_store.reset()

    def _grounded_context(self, question: str) -> tuple[str, list[dict]]:
        results = self.vector_store.query(question, top_k=3)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        contexts = []
        for document, metadata in zip(documents, metadatas):
            contexts.append({"content": document, "source": metadata.get("source", "unknown")})

        if not contexts:
            return "No relevant document content was found for this question.", []

        return "\n\n".join(item["content"] for item in contexts), contexts

    def _generate_with_groq(self, question: str, context: str) -> str:
        if not settings.groq_api_key:
            return context

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a precise enterprise document QA assistant. Use only the supplied document context. "
                                "DO NOT HALLUCINATE. Answer factually, cite only what is supported by the context, and avoid speculation. "
                                "If the answer cannot be found in the context, say: 'The uploaded documents do not provide enough information to answer this question.'"
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Question: {question}\n\n"
                                "Grounding context:\n"
                                f"{context}"
                            ),
                        },
                    ],
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload["choices"][0]["message"]["content"].strip()
            return answer if answer else "The uploaded documents do not provide enough information to answer this question."
        except Exception:
            return context

    def answer_question(self, question: str) -> Dict[str, Any]:
        context, contexts = self._grounded_context(question)

        if not contexts:
            answer = "No relevant document content was found for this question."
        elif settings.groq_api_key:
            answer = self._generate_with_groq(question, context)
        else:
            answer = contexts[0]["content"]

        return {
            "answer": answer,
            "sources": contexts,
            "question": question,
            "retrieved_chunks": len(contexts),
        }
