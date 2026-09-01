from app.core.vector_store import VectorKnowledgeStore
from app.backend.agent_service import DocumentAgent


def test_documents_persist_across_store_instances(tmp_path):
    first_store = VectorKnowledgeStore(tmp_path)
    first_store.add_documents(
        ["Solar panels power the Alpha project."],
        [{"source": "alpha.txt", "chunk_index": 0}],
    )

    second_store = VectorKnowledgeStore(tmp_path)
    result = second_store.query("What powers Alpha project?")

    assert result["documents"] == [["Solar panels power the Alpha project."]]
    assert result["metadatas"] == [[{"source": "alpha.txt", "chunk_index": 0}]]


def test_reset_removes_persisted_documents(tmp_path):
    store = VectorKnowledgeStore(tmp_path)
    store.add_documents(["Temporary document content."], [{"source": "temp.txt"}])
    store.reset()

    reloaded_store = VectorKnowledgeStore(tmp_path)

    assert reloaded_store.documents == []
    assert reloaded_store.query("Temporary document content")["documents"] == [[]]


def test_character_similarity_supports_close_paraphrases(tmp_path):
    store = VectorKnowledgeStore(tmp_path)
    store.add_documents(
        ["The Alpha project is powered by solar panels."],
        [{"source": "alpha.txt"}],
    )

    result = store.query("How does the Alpha project get its power?")

    assert result["metadatas"] == [[{"source": "alpha.txt"}]]


def test_no_llm_fallback_formats_relevant_sentences(tmp_path, monkeypatch):
    monkeypatch.setattr("app.backend.agent_service.settings.groq_api_key", "")
    agent = DocumentAgent(VectorKnowledgeStore(tmp_path))
    agent.vector_store.add_documents(
        ["The visitor policy applies to all guests. Child visitors must be accompanied by an adult. "
         "The cafeteria closes at 6 PM."],
        [{"source": "visitor-policy.txt"}],
    )

    result = agent.answer_question("Are child visitors allowed?")

    assert result["answer"].startswith("According to the uploaded document:")
    assert "- Child visitors must be accompanied by an adult." in result["answer"]
    assert "cafeteria" not in result["answer"]