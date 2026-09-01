import json
from pathlib import Path
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings


class VectorKnowledgeStore:
    def __init__(self, index_dir: str | Path | None = None):
        self.documents: List[str] = []
        self.metadata: List[dict] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        self.matrix = None
        self.char_matrix = None
        self.index_path = Path(index_dir or settings.index_dir) / "documents.json"
        self._load()

    def _rebuild_matrix(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        if self.documents:
            self.matrix = self.vectorizer.fit_transform(self.documents)
            self.char_matrix = self.char_vectorizer.fit_transform(self.documents)
        else:
            self.matrix = None
            self.char_matrix = None

    def _load(self):
        if not self.index_path.exists():
            return
        with self.index_path.open("r", encoding="utf-8") as index_file:
            payload = json.load(index_file)
        self.documents = payload.get("documents", [])
        self.metadata = payload.get("metadata", [])
        if len(self.documents) != len(self.metadata):
            raise ValueError("Persisted document index has mismatched documents and metadata")
        self._rebuild_matrix()

    def _save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.index_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as index_file:
            json.dump({"documents": self.documents, "metadata": self.metadata}, index_file)
        temporary_path.replace(self.index_path)

    def add_documents(self, documents: List[str], metadata_list: List[dict] | None = None):
        metadata_list = metadata_list or [{} for _ in documents]

        sources = {metadata.get("source") for metadata in metadata_list if metadata.get("source")}
        if sources:
            retained = [
                (document, metadata)
                for document, metadata in zip(self.documents, self.metadata)
                if metadata.get("source") not in sources
            ]
            self.documents = [document for document, _ in retained]
            self.metadata = [metadata for _, metadata in retained]

        self.documents.extend(documents)
        self.metadata.extend(metadata_list)
        self._rebuild_matrix()
        self._save()
        return [f"doc_{idx}" for idx in range(len(self.documents))]

    def query(self, question: str, top_k: int = 4):
        if not self.documents or self.matrix is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        question_vector = self.vectorizer.transform([question])
        word_similarity = cosine_similarity(question_vector, self.matrix).flatten()
        char_similarity = cosine_similarity(
            self.char_vectorizer.transform([question]), self.char_matrix
        ).flatten()
        similarity = (word_similarity * 0.75) + (char_similarity * 0.25)
        query_terms = set(self.vectorizer.build_analyzer()(question))
        required_matches = min(2, len(query_terms))
        ranked_indices = np.argsort(similarity)[::-1]
        matching_indices = []
        for index in ranked_indices:
            document_terms = set(self.vectorizer.build_analyzer()(self.documents[index]))
            matched_terms = len(query_terms & document_terms)
            lexical_match = matched_terms >= required_matches
            close_language_match = matched_terms == 0 and similarity[index] >= 0.20
            if similarity[index] > 0 and (lexical_match or close_language_match):
                matching_indices.append(index)
            if len(matching_indices) == top_k:
                break

        doc_results = [self.documents[idx] for idx in matching_indices]
        meta_results = [self.metadata[idx] for idx in matching_indices]
        distances = [float(1 - similarity[idx]) for idx in matching_indices]

        return {
            "documents": [doc_results],
            "metadatas": [meta_results],
            "distances": [distances],
        }

    def reset(self):
        self.documents = []
        self.metadata = []
        self.matrix = None
        self.char_matrix = None
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        if self.index_path.exists():
            self.index_path.unlink()
