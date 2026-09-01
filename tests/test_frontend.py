from dataclasses import dataclass

from streamlit.testing.v1 import AppTest


APP_PATH = "app/frontend/streamlit_app.py"


@dataclass
class FakeResponse:
    status_code: int
    payload: dict

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self.payload


def make_app():
    return AppTest.from_file(APP_PATH)


def test_initial_ui_shows_empty_history_and_required_controls():
    app = make_app().run()

    assert not app.exception
    assert app.text_area[0].label == "Enter your question"
    assert any(button.label == "Upload & Index" for button in app.button)
    assert any(button.label == "Submit Question" for button in app.button)
    assert app.session_state.conversation_history == []


def test_empty_question_is_logged_without_http_request(monkeypatch):
    calls = []

    def fail_request(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("empty questions must not call the API")

    monkeypatch.setattr("requests.post", fail_request)
    app = make_app().run()
    app.text_area[0].set_value("   ")
    app.button(key="FormSubmitter:question_form-Submit Question").click().run()

    assert calls == []
    assert any("Question Attempted" in entry for entry in app.session_state.logs)


def test_upload_success_updates_uploaded_files(monkeypatch):
    monkeypatch.setattr(
        "requests.post",
        lambda *args, **kwargs: FakeResponse(
            200,
            {"message": "File uploaded and indexed successfully.", "chunks": 2},
        ),
    )
    app = make_app()
    app.session_state["selected_file"] = {
        "name": "policy.txt",
        "content": b"Annual leave policy",
        "content_type": "text/plain",
    }
    app.run()
    app.button(key="upload_btn").click().run()

    assert app.session_state.uploaded_documents == ["policy.txt"]
    assert any("Upload Complete" in entry for entry in app.session_state.logs)


def test_upload_failure_is_logged(monkeypatch):
    monkeypatch.setattr(
        "requests.post",
        lambda *args, **kwargs: FakeResponse(422, {"detail": "No readable text was found"}),
    )
    app = make_app()
    app.session_state["selected_file"] = {
        "name": "scan.pdf",
        "content": b"pdf",
        "content_type": "application/pdf",
    }
    app.run()
    app.button(key="upload_btn").click().run()

    assert app.session_state.uploaded_documents == []
    assert any("Upload Failed" in entry for entry in app.session_state.logs)


def test_successful_question_creates_and_deduplicates_history(monkeypatch):
    calls = []

    def answer_request(*args, **kwargs):
        calls.append(kwargs["json"]["question"])
        return FakeResponse(
            200,
            {
                "answer": f"Answer {len(calls)}",
                "sources": [{"source": "policy.txt", "content": "Annual leave policy"}],
                "retrieved_chunks": 1,
            },
        )

    monkeypatch.setattr("requests.post", answer_request)
    app = make_app().run()
    submit_key = "FormSubmitter:question_form-Submit Question"

    for _ in range(2):
        app.text_area[0].set_value("What is the leave policy?")
        app.button(key=submit_key).click().run()

    history = app.session_state.conversation_history
    assert calls == ["What is the leave policy?", "What is the leave policy?"]
    assert len(history) == 1
    assert history[0]["answer"] == "Answer 2"
    assert history[0]["timestamp"]
    assert history[0]["sources"] == [{"source": "policy.txt", "content": "Annual leave policy"}]
    assert app.session_state.latest_response["answer"] == "Answer 2"


def test_history_displays_saved_supporting_sources():
    app = make_app()
    app.session_state["conversation_history"] = [
        {
            "timestamp": "2026-09-01 10:00:00",
            "question": "What is the policy?",
            "answer": "Annual leave is available.",
            "sources": [{"source": "policy.txt", "content": "Annual leave policy"}],
        }
    ]
    app.run()

    assert any("policy.txt" in text.value for text in app.caption)
    assert any("Annual leave policy" in text.value for text in app.markdown)


def test_question_api_failure_does_not_add_history(monkeypatch):
    monkeypatch.setattr(
        "requests.post",
        lambda *args, **kwargs: FakeResponse(404, {"detail": "Not Found"}),
    )
    app = make_app().run()
    app.text_area[0].set_value("What is the policy?")
    app.button(key="FormSubmitter:question_form-Submit Question").click().run()

    assert app.session_state.conversation_history == []
    assert app.session_state.latest_response is None
    assert any("Question Failed" in entry and "HTTP 404" in entry for entry in app.session_state.logs)


def test_single_history_delete_and_delete_all():
    app = make_app()
    app.session_state["conversation_history"] = [
        {"timestamp": "2026-09-01 10:00:00", "question": "First?", "answer": "One"},
        {"timestamp": "2026-09-01 10:01:00", "question": "Second?", "answer": "Two"},
    ]
    app.run()

    app.button(key="delete_history_1").click().run()
    assert [entry["question"] for entry in app.session_state.conversation_history] == ["First?"]

    app.button(key="delete_all_history").click().run()
    assert app.session_state.conversation_history == []


def test_clear_session_resets_documents_history_answer_and_logs(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: FakeResponse(200, {}))
    app = make_app()
    app.session_state["uploaded_documents"] = ["policy.txt"]
    app.session_state["conversation_history"] = [
        {"timestamp": "now", "question": "Question", "answer": "Answer"}
    ]
    app.session_state["latest_response"] = {
        "question": "Question",
        "answer": "Answer",
        "sources": [],
        "retrieved_chunks": 0,
    }
    app.session_state["logs"] = ["old log"]
    app.run()

    next(button for button in app.button if button.label == "🔄 Clear Session").click().run()
    next(button for button in app.button if button.label == "Confirm Clear").click().run()

    assert app.session_state.uploaded_documents == []
    assert app.session_state.conversation_history == []
    assert app.session_state.latest_response is None
    assert app.session_state.logs == [entry for entry in app.session_state.logs if "Session Reset" in entry]
