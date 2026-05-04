import uuid
import time
import contextvars
from pathlib import Path

from flask import request, g
from loguru import logger

from realview_chat.observability.metrics import *

correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


def set_correlation_id(correlation_id: str | None = None) -> str:
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str:
    return correlation_id_var.get() or "-"

logger.remove()  

logger = logger.patch(
    lambda r: r["extra"].setdefault("correlation_id", "-")
)

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

def log_event(event, layer, **kwargs):
    cid = get_correlation_id()

    if not event:
        raise ValueError("event cannot be empty")

    allowed_layers = {"api", "pipeline", "db", "app"}
    if layer not in allowed_layers:
        raise ValueError(f"invalid layer: {layer}")
    
    logger.bind(
        correlation_id = cid,
        layer = layer,
        **kwargs
    ).info(event)



def init_request_logging(app):

    @app.before_request
    def _before_request():
        g.start_time = time.time()
        set_correlation_id()

    @app.after_request
    def _after_request(response):
        duration = time.time() - g.start_time

        API_REQUESTS_TOTAL.labels(
            method=request.method,
            path=request.path,
            status_code=response.status_code
        ).inc()

        api_request_duration_seconds.labels(
            method=request.method,
            path=request.path
        ).observe(duration)

        log_event(
            "request_completed",
            "api",
            method=request.method,
            path=request.path,
            status_code=response.status_code
        )

        return response

def run_pipeline_step(step_name: str, func):
    start = time.time()

    log_event("pipeline_step_started", "pipeline", step=step_name)

    try:
        result = func()
        pipeline_runs_total.labels(status="success").inc()
        return result

    except Exception:
        pipeline_runs_total.labels(status="failed").inc()
        log_event("pipeline_step_failed", "pipeline", step=step_name)
        raise

    finally:
        elapsed = time.time() - start

        pipeline_step_duration_seconds.labels(step=step_name).observe(elapsed)

        log_event(
            "pipeline_step_finished",
            "pipeline",
            step=step_name,
            elapsed_ms=elapsed * 1000
        )

def db_operation(operation_name: str, func):
    start = time.time()

    try:
        result = func()

        db_operations_total.labels(
            operation=operation_name,
            status="success"
        ).inc()

        return result

    except Exception:
        db_operations_total.labels(
            operation=operation_name,
            status="failed"
        ).inc()

        log_event(
            "db_operation_failed",
            "db",
            operation=operation_name
        )
        raise

    finally:
        elapsed = time.time() - start

        db_operation_duration_seconds.labels(
            operation=operation_name
        ).observe(elapsed)
