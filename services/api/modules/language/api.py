"""Authenticated, owner-scoped language profile API; model/translation adapters are optional."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.api.modules.language.service import LanguageProfile, LanguageService


class LanguageProfileRequest(BaseModel):
    language: str = Field(default="en", min_length=2, max_length=6)
    dialect: str | None = Field(default=None, max_length=64)
    register: str = Field(default="neutral", max_length=16)
    formality: str = Field(default="balanced", max_length=16)
    response_language: str | None = Field(default=None, min_length=2, max_length=6)
    code_switching: bool = True


class LanguageProfileResponse(LanguageProfileRequest):
    pass


def create_language_router(service: LanguageService, current_user: object) -> APIRouter:
    router = APIRouter(prefix="/language", tags=["language"])

    def owner(context: object) -> str:
        owner_id = getattr(context, "user_id", None)
        if not isinstance(owner_id, str) or not owner_id:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        return owner_id

    @router.get("/profile", response_model=LanguageProfileResponse)
    def get_profile(context=Depends(current_user)):
        profile = service.get_preference(owner(context)) or LanguageProfile()
        return profile.__dict__

    @router.put("/profile", response_model=LanguageProfileResponse)
    def put_profile(body: LanguageProfileRequest, context=Depends(current_user)):
        try:
            profile = LanguageProfile(**body.model_dump())
            service.save_preference(owner(context), profile)
            return profile.__dict__
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_language_profile", "message": str(exc)}) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail={"code": "language_memory_unavailable", "message": "Language preference storage is unavailable"}) from exc

    return router
