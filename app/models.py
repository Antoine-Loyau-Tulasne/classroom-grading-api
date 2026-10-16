from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # "teacher" | "student"


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text)
    # Comma-separated keywords the grader looks for (toy rubric).
    rubric: Mapped[str] = mapped_column(Text, default="")
    max_attempts: Mapped[int] = mapped_column(default=1)
    deadline: Mapped[Optional[datetime]] = mapped_column(default=None)

    submissions: Mapped[List["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )

    @property
    def rubric_keywords(self) -> List[str]:
        return [k.strip() for k in self.rubric.split(",") if k.strip()]


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    answer: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Automatic suggestion
    auto_score: Mapped[Optional[float]] = mapped_column(default=None)
    auto_feedback: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Teacher decision (human in the loop)
    final_score: Mapped[Optional[float]] = mapped_column(default=None)
    final_feedback: Mapped[Optional[str]] = mapped_column(Text, default=None)
    released: Mapped[bool] = mapped_column(default=False)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
