from dataclasses import dataclass


@dataclass
class Question:
    id: int
    task_number: int
    subcategory: str | None
    word_display: str
    correct_answer: str
    wrong_options: list[str]
    explanation: str
    difficulty: int = 1


@dataclass
class UserStats:
    total_answers: int
    correct_answers: int
    accuracy_pct: float
    current_streak: int
    longest_streak: int


@dataclass
class CategoryStats:
    task_number: int
    subcategory: str | None
    total_answers: int
    correct_answers: int
    accuracy_pct: float


@dataclass
class ProblemWord:
    question_id: int
    word_display: str
    correct_answer: str
    times_shown: int
    times_correct: int
    accuracy_pct: float
