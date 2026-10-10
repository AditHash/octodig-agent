"""Public HTTP contracts. Provider and database internals stay private."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    workspace_name: str = Field(min_length=1, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website: HttpUrl | None = None
    notes: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    website: str | None
    normalized_domain: str | None
    notes: str
    tags: list[str]


class ResearchStartRequest(BaseModel):
    provider: Literal["openai", "gemini"]
    mode: Literal["standard", "deep"] = "standard"
    max_cost_usd: Decimal = Field(gt=0, max_digits=8, decimal_places=4)


class ResearchRunResponse(BaseModel):
    id: str
    status: str
    provider: str
    mode: str
