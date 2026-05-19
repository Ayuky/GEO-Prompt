from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Any

from app.services.langfuse_service import LangfuseService

router = APIRouter(prefix="/langfuse", tags=["langfuse"])

langfuse_service = LangfuseService()


@router.get("/stats", response_model=dict[str, Any])
def get_langfuse_stats():
    """获取 Langfuse 统计数据"""
    try:
        stats = langfuse_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/traces")
def get_langfuse_traces(
    limit: int = Query(default=10, ge=1, le=100)
):
    """获取最近的追踪记录"""
    try:
        traces = langfuse_service.get_traces(limit=limit)
        return {"data": traces, "total": len(traces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取追踪记录失败: {str(e)}")