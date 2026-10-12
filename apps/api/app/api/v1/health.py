from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import check_database_health
from app.core.redis import check_redis_health
from app.core.storage import check_storage_health

router = APIRouter()


class ServiceHealthSchema(BaseModel):
    database: str
    redis: str
    storage: str


class HealthResponseSchema(BaseModel):
    status: str
    environment: str
    version: str
    timestamp: str
    services: ServiceHealthSchema


@router.get("/health", response_model=HealthResponseSchema, tags=["Health"])
@router.get("/healthz", response_model=HealthResponseSchema, tags=["Health"])
async def get_health():
    db_status = await check_database_health()
    redis_status = await check_redis_health()
    storage_status = await check_storage_health()

    # Determine overall status
    is_ok = db_status in ("connected", "mocked") and redis_status in ("connected", "mocked")
    overall_status = "ok" if is_ok else "degraded"

    return HealthResponseSchema(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=ServiceHealthSchema(
            database=db_status,
            redis=redis_status,
            storage=storage_status,
        ),
    )
