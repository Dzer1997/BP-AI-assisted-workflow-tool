from loguru import logger
import uuid
import contextvars
import time
from pathlib import Path
from flask import request

correlation_id_var = contextvars.ContextVar("correlation_id", default=None)

def set_correlation_id(correlation_id: str | None = None) -> str:
    """
    Must ONLY be called at request boundary (Flask before_request).
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str:
    return correlation_id_var.get() or "no-correlation-id"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.add(
    LOG_DIR / "app.log",
    rotation="00:00",
    retention="14 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[correlation_id]} | {extra[layer]} | {message}",
)

logger.add(
    LOG_DIR / "error.log",
    rotation="00:00",
    retention="30 days",
    level="ERROR",
    format="{time} | {level} | {extra[correlation_id]} | {message}",
)

def init_request_logging(app):

    @app.before_request
    def _before_request():
        set_correlation_id()

    @app.after_request
    def _after_request(response):
        logger.bind(
            correlation_id=get_correlation_id(),
            layer="api",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
        ).info("request_completed")

        return response

def run_pipeline_step(step_name: str, func):
    start = time.time()

    try:
        result = func()
        return result

    except Exception:
        logger.bind(
            correlation_id=get_correlation_id(),
            layer="pipeline",
            step=step_name,
        ).exception("pipeline_step_failed")
        raise

    finally:
        logger.bind(
            correlation_id=get_correlation_id(),
            layer="pipeline",
            step=step_name,
            elapsed_ms=(time.time() - start) * 1000,
        ).info("pipeline_step_finished")

def db_operation(operation_name: str, func):
    try:
        result = func()

        logger.bind(
            correlation_id=get_correlation_id(),
            layer="db",
            operation=operation_name,
        ).info("db_operation_success")

        return result

    except Exception:
        logger.bind(
            correlation_id=get_correlation_id(),
            layer="db",
            operation=operation_name,
        ).exception("db_operation_failed")
        raise

def log_event(message: str, **kwargs):
    logger.bind(
        correlation_id=get_correlation_id(),
        layer=kwargs.pop("layer", "app"),
        **kwargs,
    ).info(message)

def log_error(message: str, **kwargs):
    logger.bind(
        correlation_id=get_correlation_id(),
        layer=kwargs.pop("layer", "app"),
        **kwargs,
    ).error(message)