from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CustomModelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    base_url: str = Field(min_length=1, max_length=512)
    model_name: str = Field(min_length=1, max_length=128)
    api_key: str = Field(min_length=1, max_length=512)


class CustomModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=64)
    base_url: str | None = Field(default=None, min_length=1, max_length=512)
    model_name: str | None = Field(default=None, min_length=1, max_length=128)
    api_key: str | None = Field(default=None, min_length=1, max_length=512)
    is_active: bool | None = None


class CustomModelRead(BaseModel):
    id: int
    name: str
    base_url: str
    model_name: str
    api_key_masked: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
