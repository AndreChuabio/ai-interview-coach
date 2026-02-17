"""
User profile and career path endpoints.

Duolingo-style: user has age and a selected profession (career path);
age drives difficulty and language in prompts.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException

from backend.career_paths import (
    CAREER_PATHS,
    PROFESSIONS,
    get_path,
    is_lesson_unlocked,
)
from backend.services.profile_service import (
    get_profile as get_profile_svc,
    upsert_profile,
    record_lesson_complete as record_lesson_svc,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/profile")
async def get_profile(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Get current user profile (age, profession). Returns 200 with defaults if no profile."""
    if not x_user_id or not x_user_id.strip():
        return {
            "user_id": "",
            "age": 18,
            "profession": "data_scientist",
            "age_bucket": "adult",
            "completed_lessons": [],
        }
    profile = await get_profile_svc(x_user_id.strip())
    if not profile:
        return {
            "user_id": x_user_id.strip(),
            "age": 18,
            "profession": "data_scientist",
            "age_bucket": "adult",
            "completed_lessons": [],
        }
    return profile


@router.post("/profile")
async def post_profile(
    body: dict,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Set profile: age and profession. Body: { \"age\": number, \"profession\": \"data_scientist\" | \"trader\" }."""
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    age = body.get("age", 18)
    profession = body.get("profession", "data_scientist")
    if profession not in PROFESSIONS:
        profession = "data_scientist"
    profile = await upsert_profile(x_user_id.strip(), int(age), profession)
    return profile


@router.get("/career-path")
async def get_career_path(
    profession: str = "data_scientist",
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Get career path for a profession with completion and lock state per lesson."""
    if profession not in CAREER_PATHS:
        raise HTTPException(status_code=404, detail="Unknown profession")
    completed_lessons: list[dict] = []
    if x_user_id and x_user_id.strip():
        profile = await get_profile_svc(x_user_id.strip())
        if profile:
            completed_lessons = profile.get("completed_lessons", [])
    completed_set = {
        (c["skill_id"], c["lesson_id"])
        for c in completed_lessons
        if c.get("profession") == profession
    }
    path = get_path(profession)
    skills_out = []
    for si, skill in enumerate(path):
        lessons_out = []
        for li, lesson in enumerate(skill["lessons"]):
            completed = (skill["id"], lesson["id"]) in completed_set
            unlocked = is_lesson_unlocked(profession, completed_lessons, si, li)
            lessons_out.append({
                "id": lesson["id"],
                "name": lesson["name"],
                "type": lesson["type"],
                "completed": completed,
                "unlocked": unlocked,
            })
        skills_out.append({
            "id": skill["id"],
            "name": skill["name"],
            "lessons": lessons_out,
        })
    return {
        "profession": profession,
        "info": PROFESSIONS.get(profession, {}),
        "skills": skills_out,
    }


@router.post("/lesson-complete")
async def post_lesson_complete(
    body: dict,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Mark a lesson complete. Body: { \"profession\", \"skill_id\", \"lesson_id\" }."""
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    profession = body.get("profession")
    skill_id = body.get("skill_id")
    lesson_id = body.get("lesson_id")
    if not all([profession, skill_id, lesson_id]):
        raise HTTPException(status_code=400, detail="profession, skill_id, lesson_id required")
    await record_lesson_svc(x_user_id.strip(), profession, skill_id, lesson_id)
    return {"ok": True}
