from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.experiment_service import ExperimentService
from app.services.model_gateway import ModelGateway
from app.services.model_service import ModelService
from app.services.prompt_generator import PromptGenerator
from app.services.prompt_judge import PromptJudge
from app.services.reward import RewardService
from app.services.training_service import TrainingService
from app.services.records_service import RecordsService
from app.services.versions_service import VersionsService
from app.services.metrics_service import MetricsService


@lru_cache
def get_model_gateway() -> ModelGateway:
    return ModelGateway()


@lru_cache
def get_prompt_generator() -> PromptGenerator:
    return PromptGenerator()


@lru_cache
def get_reward_service() -> RewardService:
    return RewardService()


@lru_cache
def get_prompt_judge() -> PromptJudge:
    return PromptJudge(model_gateway=get_model_gateway())


def get_experiment_service(db: Session = Depends(get_db)) -> ExperimentService:
    return ExperimentService(
        db=db,
        model_gateway=get_model_gateway(),
        prompt_generator=get_prompt_generator(),
        reward_service=get_reward_service(),
        prompt_judge=get_prompt_judge(),
    )


def get_model_service(db: Session = Depends(get_db)) -> ModelService:
    return ModelService(db=db)


@lru_cache
def get_training_service() -> TrainingService:
    return TrainingService(
        model_gateway=get_model_gateway(),
        prompt_generator=get_prompt_generator(),
        reward_service=get_reward_service(),
        prompt_judge=get_prompt_judge(),
    )


def get_records_service(db: Session = Depends(get_db)) -> RecordsService:
    return RecordsService(db=db)


def get_versions_service(db: Session = Depends(get_db)) -> VersionsService:
    return VersionsService(db=db)


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    return MetricsService(db=db)

