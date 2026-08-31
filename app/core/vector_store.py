from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorKnowledgeStore:
    def __init__(self):
        self.documents: List[str] = []
        self.metadata: List[dict] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = None

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
        if self.documents:
            self.matrix = self.vectorizer.fit_transform(self.documents)
        return [f"doc_{idx}" for idx in range(len(self.documents))]

    def query(self, question: str, top_k: int = 4):
        if not self.documents or self.matrix is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        question_vector = self.vectorizer.transform([question])
        similarity = cosine_similarity(question_vector, self.matrix).flatten()
        query_terms = set(self.vectorizer.build_analyzer()(question))
        required_matches = min(2, len(query_terms))
        ranked_indices = np.argsort(similarity)[::-1]
        matching_indices = []
        for index in ranked_indices:
            document_terms = set(self.vectorizer.build_analyzer()(self.documents[index]))
            matched_terms = len(query_terms & document_terms)
            if similarity[index] > 0 and matched_terms >= required_matches:
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
        self.vectorizer = TfidfVectorizer(stop_words="english")
