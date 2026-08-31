from fastapi.testclient import TestClient
import fitz

from app.backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_empty_question_rejected():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 400


def test_upload_accepts_supported_file_type():
    content = b"Acme Corp has a remote work policy and a quarterly review process."
    response = client.post(
        "/upload",
        files={"file": ("sample.txt", content, "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.txt"
    assert payload["chunks"] > 0

    question_response = client.post("/ask", json={"question": "What does Acme Corp do about remote work?"})
    assert question_response.status_code == 200
    assert question_response.json()["sources"]


def test_questions_retrieve_matching_uploaded_documents():
    first = client.post(
        "/upload",
        files={"file": ("alpha.txt", b"Alpha project uses solar panels.", "text/plain")},
    )
    second = client.post(
        "/upload",
        files={"file": ("beta.txt", b"Beta project uses wind turbines.", "text/plain")},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    alpha = client.post("/ask", json={"question": "What does Alpha project use?"}).json()
    beta = client.post("/ask", json={"question": "What does Beta project use?"}).json()

    assert alpha["sources"][0]["source"] == "alpha.txt"
    assert "solar panels" in alpha["sources"][0]["content"]
    assert beta["sources"][0]["source"] == "beta.txt"
    assert "wind turbines" in beta["sources"][0]["content"]


def test_retrieval_excludes_chunks_matching_only_one_query_term():
    response = client.post(
        "/upload",
        files={
            "file": (
                "visitor-policy.txt",
                (
                    b"VISITOR POLICY. Child visitors under 12 must be accompanied by an adult. "
                    b"Children are not permitted in restricted areas."
                ),
                "text/plain",
            )
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/upload",
        files={"file": ("leave-policy.txt", b"Child adoption leave may be granted for 180 days.", "text/plain")},
    )
    assert response.status_code == 200

    answer = client.post("/ask", json={"question": "Are child visitors allowed?"}).json()

    assert answer["sources"][0]["source"] == "visitor-policy.txt"
    assert all(source["source"] != "leave-policy.txt" for source in answer["sources"])
    assert "Child visitors under 12 must be accompanied by an adult" in answer["answer"]
    assert "adoption leave" not in answer["answer"]


def test_upload_indexes_text_based_pdf():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Annual leave is twenty days for eligible employees.")
    pdf_content = document.tobytes()
    document.close()

    response = client.post(
        "/upload",
        files={"file": ("leave-policy.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["chunks"] > 0


def test_empty_upload_is_rejected():
    response = client.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The selected file is empty"


def test_upload_accepts_windows_encoded_csv():
    content = "Name,Comment\nOperations,Annual review – complete\n".encode("cp1252")
    response = client.post(
        "/upload",
        files={"file": ("business-operations-survey.csv", content, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["chunks"] > 0
