import logging
import uuid
from datetime import datetime

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from ..schema.feedback_schemas import (
    FeedbackSubmissionSchema,
    FeedbackSubmissionResponseSchema,
)
from ..schema.response_schemas import ResponseStatus, ErrorCode, create_error_response
from ..services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

feedback_router = Router()


@feedback_router.post("/validate", include_in_schema=False)
def validate_feedback(request: HttpRequest, feedback_data: FeedbackSubmissionSchema):
    try:
        return {
            "valid": True,
            "message": "Feedback data is valid",
            "data": feedback_data.model_dump(),
        }
    except Exception as e:
        return {"valid": False, "message": "Validation failed", "errors": [str(e)]}


@feedback_router.post(
    "/submit", response=FeedbackSubmissionResponseSchema, include_in_schema=False
)
def submit_feedback(request: HttpRequest, feedback_data: FeedbackSubmissionSchema):
    request_id = str(uuid.uuid4())

    try:
        result = FeedbackService.submit_feedback(feedback_data.model_dump())

        if result["success"]:
            return FeedbackSubmissionResponseSchema(
                status=ResponseStatus.SUCCESS,
                message=result["message"],
                ticket_id=result.get("ticket_id"),
                submission_id=request_id,
                timestamp=datetime.utcnow().isoformat(),
            )
        else:
            error_response = create_error_response(
                error_code=ErrorCode.FEEDBACK_SUBMISSION_FAILED,
                message=result["message"],
                request_id=request_id,
            )
            raise HttpError(500, error_response.model_dump())

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in feedback submission: {str(e)}")
        error_response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id,
        )
        raise HttpError(500, error_response.model_dump())
