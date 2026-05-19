from fastapi import APIRouter

from app.api.v1.experiment_routes import router as experiment_router
from app.api.v1.langfuse_routes import router as langfuse_router
from app.api.v1.metrics_routes import router as metrics_router
from app.api.v1.model_routes import router as model_router
from app.api.v1.records_routes import router as records_router
from app.api.v1.training_routes import router as training_router
from app.api.v1.versions_routes import router as versions_router

api_router = APIRouter()
api_router.include_router(experiment_router)
api_router.include_router(training_router)
api_router.include_router(langfuse_router)
api_router.include_router(model_router)
api_router.include_router(records_router)
api_router.include_router(versions_router)
api_router.include_router(metrics_router)
