from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_model_service
from app.schemas.custom_model import CustomModelCreate, CustomModelRead, CustomModelUpdate
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[CustomModelRead])
def list_models(
    active_only: bool = False,
    service: ModelService = Depends(get_model_service),
):
    models = service.list(active_only=active_only)
    return [
        CustomModelRead(
            id=m.id,
            name=m.name,
            base_url=m.base_url,
            model_name=m.model_name,
            api_key_masked=service.mask_api_key(m.encrypted_api_key),
            is_active=m.is_active,
            created_at=m.created_at,
        )
        for m in models
    ]


@router.post("", response_model=CustomModelRead)
def create_model(
    payload: CustomModelCreate,
    service: ModelService = Depends(get_model_service),
):
    model = service.create(payload)
    return CustomModelRead(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        model_name=model.model_name,
        api_key_masked=service.mask_api_key(model.encrypted_api_key),
        is_active=model.is_active,
        created_at=model.created_at,
    )


@router.get("/{model_id}", response_model=CustomModelRead)
def get_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
):
    model = service.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return CustomModelRead(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        model_name=model.model_name,
        api_key_masked=service.mask_api_key(model.encrypted_api_key),
        is_active=model.is_active,
        created_at=model.created_at,
    )


@router.put("/{model_id}", response_model=CustomModelRead)
def update_model(
    model_id: int,
    payload: CustomModelUpdate,
    service: ModelService = Depends(get_model_service),
):
    try:
        model = service.update(model_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomModelRead(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        model_name=model.model_name,
        api_key_masked=service.mask_api_key(model.encrypted_api_key),
        is_active=model.is_active,
        created_at=model.created_at,
    )


@router.delete("/{model_id}")
def delete_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
):
    try:
        service.delete(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Model deleted successfully"}
