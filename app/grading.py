"""Automatic grading.

The grader only *suggests* a score: a teacher always validates it before the
student sees anything. Any object with a ``grade`` method can be plugged in
(for instance an LLM-based grader); the default one is a transparent keyword
matcher so the demo runs offline and every score can be explained.
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import List, Protocol

MAX_SCORE = 20.0


@dataclass
class GradingResult:
    score: float
    feedback: str


class Grader(Protocol):
    def grade(self, instructions: str, rubric: List[str], answer: str) -> GradingResult: ...


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class KeywordGrader:
    """Score = share of rubric keywords found in the answer, with a length sanity check."""

    min_words = 15

    def grade(self, instructions: str, rubric: List[str], answer: str) -> GradingResult:
        words = re.findall(r"\w+", answer)
        if not rubric:
            return GradingResult(MAX_SCORE / 2, "No rubric defined: neutral score, manual review needed.")

        text = _normalize(answer)
        found = [k for k in rubric if _normalize(k) in text]
        missing = [k for k in rubric if k not in found]
        score = MAX_SCORE * len(found) / len(rubric)

        notes = []
        if len(words) < self.min_words:
            score *= 0.5
            notes.append(f"Answer is very short ({len(words)} words): score halved.")
        notes.append(f"Covered: {', '.join(found) or 'none'}.")
        if missing:
            notes.append(f"Missing: {', '.join(missing)}.")

        return GradingResult(round(score, 1), " ".join(notes))


default_grader: Grader = KeywordGrader()
