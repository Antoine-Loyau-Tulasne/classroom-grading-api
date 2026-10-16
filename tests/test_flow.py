import os

os.environ["DATABASE_URL"] = "sqlite:///./test_classroom.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.grading import KeywordGrader  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def auth_header(email, role):
    client.post("/auth/register", json={"email": email, "password": "password123", "role": role})
    token = client.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


ANSWER = (
    "Photosynthesis happens in the chloroplast: the plant uses light energy to turn "
    "carbon dioxide and water into glucose, releasing oxygen as a by-product."
)


def test_full_grading_flow():
    teacher = auth_header("teacher@example.com", "teacher")
    student = auth_header("student@example.com", "student")

    r = client.post(
        "/assignments",
        headers=teacher,
        json={
            "title": "Photosynthesis",
            "instructions": "Explain photosynthesis in a few sentences.",
            "rubric": ["light", "chloroplast", "glucose", "oxygen"],
        },
    )
    assert r.status_code == 201
    assignment_id = r.json()["id"]

    r = client.post(f"/assignments/{assignment_id}/submissions", headers=student, json={"answer": ANSWER})
    assert r.status_code == 201
    submission_id = r.json()["id"]
    assert r.json()["final_score"] is None  # nothing visible yet

    # Second attempt refused (max_attempts = 1)
    r = client.post(f"/assignments/{assignment_id}/submissions", headers=student, json={"answer": ANSWER})
    assert r.status_code == 409

    # Teacher sees the suggestion
    r = client.get(f"/assignments/{assignment_id}/submissions", headers=teacher)
    assert r.json()[0]["auto_score"] == 20.0

    # Student still sees nothing before release
    assert client.get("/submissions/mine", headers=student).json()[0]["final_score"] is None

    r = client.post(f"/submissions/{submission_id}/review", headers=teacher, json={"score": 18, "feedback": "Good."})
    assert r.status_code == 200

    mine = client.get("/submissions/mine", headers=student).json()[0]
    assert mine["released"] is True
    assert mine["final_score"] == 18


def test_roles_are_enforced():
    student = auth_header("student@example.com", "student")
    r = client.post("/assignments", headers=student, json={"title": "x", "instructions": "y"})
    assert r.status_code == 403
    assert client.get("/assignments").status_code == 401


def test_keyword_grader_explains_missing_points():
    result = KeywordGrader().grade("", ["light", "glucose"], "Plants need light.")
    assert result.score == 5.0  # 1/2 keywords, halved because the answer is short
    assert "Missing: glucose" in result.feedback
