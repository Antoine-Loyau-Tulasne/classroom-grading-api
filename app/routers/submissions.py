from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Submission, User
from app.schemas import Review, SubmissionOut, SubmissionTeacherView
from app.security import require_role

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("/mine", response_model=List[SubmissionOut])
def my_submissions(db: Session = Depends(get_db), student: User = Depends(require_role("student"))):
    submissions = db.scalars(select(Submission).where(Submission.student_id == student.id)).all()
    # Hide the grade until the teacher has released it.
    return [
        SubmissionOut.model_validate(s) if s.released
        else SubmissionOut(id=s.id, assignment_id=s.assignment_id, submitted_at=s.submitted_at, released=False)
        for s in submissions
    ]


@router.post("/{submission_id}/review", response_model=SubmissionTeacherView)
def review(
    submission_id: int,
    data: Review,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role("teacher")),
):
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    if submission.assignment.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your assignment")

    submission.final_score = data.score if data.score is not None else submission.auto_score
    submission.final_feedback = data.feedback if data.feedback is not None else submission.auto_feedback
    submission.released = data.release
    db.commit()
    return submission
