import logging
import inspect
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


def raise_http_error(status_code: int, message: str):
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name if frame else "Unknown"

    cls_name = None
    if "self" in frame.f_locals:
        cls_name = (
            frame.f_locals["self"].__class__.__name__
            if "self" in frame.f_locals
            else "Unknown"
        )

    logger.error(
        f"HTTP Error {status_code}: {message}. "
        f"Originated from: {cls_name + '.' if cls_name else ''}{function_name}"
    )

    raise HttpError(status_code, message)


def raise_exception(message: str):
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name if frame else "Unknown"

    cls_name = None
    if "self" in frame.f_locals:
        cls_name = (
            frame.f_locals["self"].__class__.__name__
            if "self" in frame.f_locals
            else "Unknown"
        )

    logger.error(
        f"Exception: {message}. "
        f"Originated from: {cls_name + '.' if cls_name else ''}{function_name}"
    )

    raise Exception(message)
