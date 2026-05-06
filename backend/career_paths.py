"""
Career paths (professions) for Duolingo-style learning.

POC: Data Scientist and Trader. Each has a list of skills; each skill has lessons.
"""

from __future__ import annotations

# Profession id -> display name and role (for interview/prompts)
PROFESSIONS = {
    "data_scientist": {
        "name": "Data Scientist",
        "role": "Data Scientist",
        "description": "Learn data, statistics, and storytelling.",
    },
    "trader": {
        "name": "Trader",
        "role": "Trader",
        "description": "Learn markets, risk, and trading basics.",
    },
}

# Ordered skills and lessons per profession (POC: 2–3 skills, 2–3 lessons each)
CAREER_PATHS: dict[str, list[dict]] = {
    "data_scientist": [
        {
            "id": "python_basics",
            "name": "Python Basics",
            "lessons": [
                {"id": "1", "name": "What is Python?", "type": "concept_quiz"},
                {"id": "2", "name": "Variables and data", "type": "concept_quiz"},
                {"id": "3", "name": "Practice: explain a concept", "type": "mini_interview"},
            ],
        },
        {
            "id": "statistics",
            "name": "Statistics",
            "lessons": [
                {"id": "1", "name": "What is an average?", "type": "concept_quiz"},
                {"id": "2", "name": "Why variance matters", "type": "concept_quiz"},
                {"id": "3", "name": "Practice: statistics in real life", "type": "mini_interview"},
            ],
        },
        {
            "id": "data_storytelling",
            "name": "Data Storytelling",
            "lessons": [
                {"id": "1", "name": "Turning numbers into a story", "type": "concept_quiz"},
                {"id": "2", "name": "Practice: present a finding", "type": "mini_interview"},
            ],
        },
    ],
    "trader": [
        {
            "id": "markets_basics",
            "name": "Markets Basics",
            "lessons": [
                {"id": "1", "name": "What is a market?", "type": "concept_quiz"},
                {"id": "2", "name": "Buyers and sellers", "type": "concept_quiz"},
                {"id": "3", "name": "Practice: explain a market", "type": "mini_interview"},
            ],
        },
        {
            "id": "risk",
            "name": "Risk",
            "lessons": [
                {"id": "1", "name": "What is risk?", "type": "concept_quiz"},
                {"id": "2", "name": "Why risk matters", "type": "concept_quiz"},
                {"id": "3", "name": "Practice: risk in trading", "type": "mini_interview"},
            ],
        },
        {
            "id": "trading_concepts",
            "name": "Trading Concepts",
            "lessons": [
                {"id": "1", "name": "Price and value", "type": "concept_quiz"},
                {"id": "2", "name": "Practice: trading scenario", "type": "mini_interview"},
            ],
        },
    ],
}


def get_path(profession_id: str) -> list[dict] | None:
    """Return the skill path for a profession, or None if unknown."""
    return CAREER_PATHS.get(profession_id)


def get_profession_info(profession_id: str) -> dict | None:
    """Return display info for a profession."""
    return PROFESSIONS.get(profession_id)


def is_lesson_unlocked(
    profession_id: str,
    completed_lessons: list[dict],
    skill_idx: int,
    lesson_idx: int,
) -> bool:
    """True if the lesson at (skill_idx, lesson_idx) is unlocked (all previous completed)."""
    path = get_path(profession_id)
    if not path:
        return False
    completed_set = {
        (c["skill_id"], c["lesson_id"])
        for c in completed_lessons
        if c.get("profession") == profession_id
    }
    for si, skill in enumerate(path):
        for li, _ in enumerate(skill["lessons"]):
            if si == skill_idx and li == lesson_idx:
                return True
            if (skill["id"], skill["lessons"][li]["id"]) not in completed_set:
                return False
    return False
