from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RetryError(RuntimeError):
    pass


def with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
    logger: logging.Logger | None = None,
) -> T:
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - intentional retry wrapper
            attempt += 1
            if attempt > max_retries:
                raise RetryError("Exceeded max retries") from exc

            sleep_time = max(15, backoff_seconds * (2 ** (attempt - 1)))
            if logger:
                logger.warning("Retrying after error: %s (sleep %.2fs)", exc, sleep_time)
            time.sleep(sleep_time)
