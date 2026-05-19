from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_records_service
from app.schemas.evaluation import EvaluationRecordCreate, EvaluationRecordRead, EvaluationRecordUpdate
from app.services.records_service import RecordsService

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/list")
def list_records(
    pageNum: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    experimentId: int | None = Query(default=None),
    promptVersionId: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    totalRewardMin: float | None = Query(default=None),
    totalRewardMax: float | None = Query(default=None),
    latencyMsMin: int | None = Query(default=None),
    latencyMsMax: int | None = Query(default=None),
    service: RecordsService = Depends(get_records_service),
):
    from urllib.parse import unquote
    
    if keyword and '%' in keyword:
        try:
            keyword = unquote(keyword)
        except Exception:
            pass
    skip = (pageNum - 1) * pageSize
    items, total = service.list_with_count(
        skip=skip,
        limit=pageSize,
        experiment_id=experimentId,
        prompt_version_id=promptVersionId,
        keyword=keyword,
        total_reward_min=totalRewardMin,
        total_reward_max=totalRewardMax,
        latency_ms_min=latencyMsMin,
        latency_ms_max=latencyMsMax,
    )
    return {"items": items, "total": total}


VALID_METRICS_FOR_TREND = {
    "total_reward", "mention_rate", "naturalness_score",
    "context_match_score", "sentiment_score", "recommendation_score", "llm_judge_score",
}


@router.get("/stats")
def get_records_stats(
    statType: str | None = Query(default=None),
    experimentId: int | None = Query(default=None),
    metric: str | None = Query(default=None),
    service: RecordsService = Depends(get_records_service),
):
    if statType == "byPromptTrend":
        if experimentId is None:
            raise HTTPException(status_code=400, detail="experimentId is required for byPromptTrend")
        if metric is None:
            raise HTTPException(status_code=400, detail="metric is required for byPromptTrend")
        if metric not in VALID_METRICS_FOR_TREND:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")
    return service.stats(stat_type=statType, experiment_id=experimentId, metric=metric)


@router.get("/summary", response_model=dict)
def get_records_summary(
    service: RecordsService = Depends(get_records_service),
):
    return service.summary()


@router.get("/{record_id}", response_model=EvaluationRecordRead)
def get_record(
    record_id: int,
    service: RecordsService = Depends(get_records_service),
):
    record = service.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Evaluation record not found")
    return record


@router.post("", response_model=EvaluationRecordRead)
def create_record(
    payload: EvaluationRecordCreate,
    service: RecordsService = Depends(get_records_service),
):
    return service.create(payload)


@router.put("", response_model=EvaluationRecordRead)
def update_record(
    payload: EvaluationRecordUpdate,
    service: RecordsService = Depends(get_records_service),
):
    if payload.id is None:
        raise HTTPException(status_code=400, detail="id is required for update")
    try:
        return service.update(payload.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    service: RecordsService = Depends(get_records_service),
):
    try:
        service.delete(record_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Evaluation record deleted successfully"}
