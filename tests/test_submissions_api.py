import pytest
from fastapi.testclient import TestClient
from app.api import submissions
from app.main import app as main_app


@pytest.fixture
def client():
    return TestClient(main_app)


@pytest.fixture
def test_app():
    return main_app


def test_get_submission_invalid_uuid(client):
    response = client.get("/submissions/not-a-uuid")
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["loc"][-1] == "uuid"


def test_create_submission_missing_fields(client):
    response = client.post("/submissions", json={})
    assert response.status_code == 422
    body = response.json()
    assert any(err["loc"][-1] == "title" for err in body["detail"])


class FakeService:
    async def create(self, data):
        return {
            "id": 9,
            "uuid": "1dd8bc73-010c-4032-a4f5-9b92766a3017",
            "title": "test",
            "language": "Python",
            "mongo_id": "68b7fb7f54f27c40f9613770",
            "created_at": "2025-09-03T08:25:35.135829Z",
            "updated_at": "2025-09-03T08:25:35.135829Z",
            "payload": {
                "content": "print('this is a test for my Submission router implementation')",
                "ai_response": "1. The code does not implement any backend functionality and merely prints a message to the console.\n\n2. Key findings:\n   - Lacks input handling for dynamic data.\n   - No error handling or logging mechanisms implemented.\n   - No routing logic or API framework setup (e.g., Flask or FastAPI).\n   - Doesn't encapsulate functionality in functions or classes for better structure.\n\n3. Most critical recommendation: Refactor the code to set up a basic framework for an API endpoint using Flask or FastAPI, allowing for proper request handling and response management. For example:\n\n```python\nfrom flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/test', methods=['GET'])\ndef test_route():\n    return jsonify(message='This is a test for my Submission router implementation')\n\nif __name__ == '__main__':\n    app.run(debug=True)\n```",
            },
        }


def override_service():
    return FakeService()


def test_create_submission_valid(client, test_app):
    test_app.dependency_overrides[submissions.get_submissions_service] = (
        override_service
    )
    payload = {
        "title": "test",
        "language": "Python",
        "payload": {
            "content": "print('this is a test for my Submission router implementation')"
        },
    }
    response = client.post("/submissions", json=payload)
    print(response.json())
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "test"

    test_app.dependency_overrides = {}


def test_create_submission_missing_title(client):
    payload = {
        "status": "pending",
        "language": "Python",
        "payload": {
            "content": "print('this is a test for my Submission router implementation')"
        },
    }

    response = client.post("/submissions", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert body["detail"][0]["loc"][-1] == "title"
    assert body["detail"][0]["msg"] == "Field required"


def test_create_submission_wrong_type(client):
    payload = {
        "title": 123,  # should be str
        "status": "pending",
        "language": "Python",
        "payload": {
            "content": "print('this is a test for my Submission router implementation')"
        },
    }

    response = client.post("/submissions", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert body["detail"][0]["loc"][-1] == "title"
    assert "Input should be a valid string" in body["detail"][0]["msg"]


def test_create_submission_invalid_enum(client):
    payload = {
        "title": "test",
        "status": "pending",
        "language": "Rust",
        "payload": {"content": "print('hi')"},
    }

    response = client.post("/submissions", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert body["detail"][0]["loc"][-1] == "language"
    assert (
        "Input should be 'Python', 'JavaScript' or 'Java'" in body["detail"][0]["msg"]
    )


def test_create_submission_missing_payload_content(client):
    payload = {
        "title": "test",
        "status": "pending",
        "language": "Python",
        "payload": {},
    }

    response = client.post("/submissions", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert body["detail"][0]["loc"] == ["body", "payload", "content"]
    assert body["detail"][0]["msg"] == "Field required"
