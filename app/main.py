from fastapi import FastAPI

from app.db import Base, engine
from app.routers import assignments, auth, submissions

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Classroom Grading API",
    description="Toy homework platform: teachers post assignments, students submit, "
    "an explainable grader suggests a score and the teacher validates it.",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(submissions.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
