# Classroom Grading API

A small **FastAPI** backend for homework with **human-in-the-loop automatic grading**:

1. a teacher publishes an assignment with a short rubric,
2. a student submits an answer,
3. a grader immediately suggests a score **with an explanation** (what was covered, what is missing),
4. the teacher accepts or overrides it, then releases it — only then does the student see the grade.

> Portfolio project: a compact, self-contained demo of the architecture and patterns,
> not a production system.

## Features

- JWT authentication (OAuth2 password flow) and role-based access (`teacher` / `student`)
- Assignments with attempt limit and optional deadline
- Pluggable grading strategy (`Grader` protocol) — the default `KeywordGrader` is fully explainable and runs offline; an LLM-based grader can be dropped in without touching the routes
- Grades hidden from students until the teacher validates them
- SQLAlchemy 2.0 ORM, SQLite by default (any SQL database via `DATABASE_URL`)
- End-to-end tests with `pytest` and FastAPI's `TestClient`

## Project structure

```
app/
├── main.py            # FastAPI app and router wiring
├── db.py              # engine, session, declarative base
├── models.py          # User, Assignment, Submission
├── schemas.py         # Pydantic request / response models
├── security.py        # password hashing, JWT, role guards
├── grading.py         # Grader protocol + explainable KeywordGrader
└── routers/
    ├── auth.py        # /auth/register, /auth/login, /auth/me
    ├── assignments.py # create/list assignments, submit, list submissions
    └── submissions.py # student view, teacher review & release
tests/
└── test_flow.py
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the interactive Swagger UI.

Optional environment variables:

| Variable       | Default                    | Purpose                  |
|----------------|----------------------------|--------------------------|
| `DATABASE_URL` | `sqlite:///./classroom.db` | SQLAlchemy database URL  |
| `SECRET_KEY`   | random at startup          | JWT signing key          |

## Example

```bash
# register + login
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"t@example.com","password":"password123","role":"teacher"}'
curl -X POST localhost:8000/auth/login -d "username=t@example.com&password=password123"

# create an assignment (with the teacher token)
curl -X POST localhost:8000/assignments -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Photosynthesis","instructions":"Explain it.","rubric":["light","glucose","oxygen"]}'
```

Suggested feedback looks like:

```
Covered: light, glucose. Missing: oxygen.
```

## Tests

```bash
pytest -q
```

## License

MIT
