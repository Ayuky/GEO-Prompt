from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt, encrypt
from app.models.custom_model import CustomModel
from app.schemas.custom_model import CustomModelCreate, CustomModelUpdate


def _mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


class ModelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: CustomModelCreate) -> CustomModel:
        model = CustomModel(
            name=payload.name,
            base_url=payload.base_url,
            model_name=payload.model_name,
            encrypted_api_key=encrypt(payload.api_key),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get(self, model_id: int) -> CustomModel | None:
        return self.db.get(CustomModel, model_id)

    def list(self, active_only: bool = False) -> list[CustomModel]:
        stmt = select(CustomModel).order_by(CustomModel.id.desc())
        if active_only:
            stmt = stmt.where(CustomModel.is_active == True)
        return list(self.db.scalars(stmt).all())

    def update(self, model_id: int, payload: CustomModelUpdate) -> CustomModel:
        model = self.db.get(CustomModel, model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        if payload.name is not None:
            model.name = payload.name
        if payload.base_url is not None:
            model.base_url = payload.base_url
        if payload.model_name is not None:
            model.model_name = payload.model_name
        if payload.api_key is not None:
            model.encrypted_api_key = encrypt(payload.api_key)
        if payload.is_active is not None:
            model.is_active = payload.is_active
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model_id: int) -> None:
        model = self.db.get(CustomModel, model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        self.db.delete(model)
        self.db.commit()

    def get_api_key(self, model_id: int) -> str:
        model = self.db.get(CustomModel, model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        return decrypt(model.encrypted_api_key)

    @staticmethod
    def mask_api_key(key: str) -> str:
        return _mask_api_key(key)
