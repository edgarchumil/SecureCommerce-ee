from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings

celery_app = Celery(
    "securecommerce", broker=settings.redis_url, backend=settings.redis_url, include=["app.tasks"]
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="health.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    return "pong"
