from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.grading import default_grader
from app.models import Assignment, Submission, User
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    SubmissionCreate,
    SubmissionOut,
    SubmissionTeacherView,
)
from app.security import current_user, require_role

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _get_assignment(db: Session, assignment_id: int) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return assignment


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role("teacher")),
):
    assignment = Assignment(
        teacher_id=teacher.id,
        title=data.title,
        instructions=data.instructions,
        rubric=",".join(data.rubric),
        max_attempts=data.max_attempts,
        deadline=data.deadline,
    )
    db.add(assignment)
    db.commit()
    return assignment


@router.get("", response_model=List[AssignmentOut])
def list_assignments(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Assignment).order_by(Assignment.id)).all()


@router.post("/{assignment_id}/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def submit(
    assignment_id: int,
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    student: User = Depends(require_role("student")),
):
    assignment = _get_assignment(db, assignment_id)
    if assignment.deadline and datetime.utcnow() > assignment.deadline:
        raise HTTPException(status.HTTP_409_CONFLICT, "Deadline has passed")

    attempts = db.scalar(
        select(func.count()).where(
            Submission.assignment_id == assignment_id, Submission.student_id == student.id
        )
    )
    if attempts >= assignment.max_attempts:
        raise HTTPException(status.HTTP_409_CONFLICT, "No attempts left")

    result = default_grader.grade(assignment.instructions, assignment.rubric_keywords, data.answer)
    submission = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        answer=data.answer,
        auto_score=result.score,
        auto_feedback=result.feedback,
    )
    db.add(submission)
    db.commit()
    return submission


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionTeacherView])
def list_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_role("teacher")),
):
    assignment = _get_assignment(db, assignment_id)
    if assignment.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your assignment")
    return assignment.submissions
