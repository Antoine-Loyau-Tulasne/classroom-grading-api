from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: Literal["teacher", "student"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AssignmentCreate(BaseModel):
    title: str
    instructions: str
    rubric: List[str] = Field(default_factory=list, description="Keywords expected in a good answer")
    max_attempts: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    instructions: str
    max_attempts: int
    deadline: Optional[datetime]


class SubmissionCreate(BaseModel):
    answer: str = Field(min_length=1)


class SubmissionOut(BaseModel):
    """What a student sees: the grade only once the teacher released it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    submitted_at: datetime
    released: bool
    final_score: Optional[float] = None
    final_feedback: Optional[str] = None


class SubmissionTeacherView(SubmissionOut):
    student_id: int
    answer: str
    auto_score: Optional[float]
    auto_feedback: Optional[str]


class Review(BaseModel):
    score: Optional[float] = Field(default=None, ge=0, le=20, description="Leave empty to accept the suggestion")
    feedback: Optional[str] = None
    release: bool = True
