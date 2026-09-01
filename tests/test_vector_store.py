from app.core.vector_store import VectorKnowledgeStore


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