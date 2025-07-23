from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from pydantic import ConfigDict
import re

from .response_schemas import BaseResponseSchema, ResponseStatus, ErrorCode


class FeedbackSubmissionSchema(BaseModel):
    """
    Schema for feedback submission requests.
    """

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    cc: Optional[str] = Field(
        None, max_length=500, description="Comma-separated list of CC email addresses"
    )
    subject: str = Field(
        ..., min_length=1, max_length=200, description="Feedback subject/title"
    )
    feedback: str = Field(
        ..., min_length=10, max_length=5000, description="Detailed feedback message"
    )

    model_config = ConfigDict(from_attributes=True)

    @validator("name")
    def validate_name(cls, v):
        """Validate name contains only letters, spaces, and common punctuation."""
        if not re.match(r"^[a-zA-Z\s\-\.\']+$", v.strip()):
            raise ValueError(
                "Name can only contain letters, spaces, hyphens, dots, and apostrophes"
            )
        return v.strip()

    @validator("subject")
    def validate_subject(cls, v):
        """Validate subject is not empty and properly formatted."""
        if not v.strip():
            raise ValueError("Subject cannot be empty")
        return v.strip()

    @validator("feedback")
    def validate_feedback(cls, v):
        """Validate feedback content."""
        if not v.strip():
            raise ValueError("Feedback cannot be empty")
        if len(v.strip()) < 10:
            raise ValueError("Feedback must be at least 10 characters long")
        return v.strip()

    @validator("cc")
    def validate_cc_emails(cls, v):
        """Validate CC email addresses if provided."""
        if v is None or not v.strip():
            return v

        cc_emails = [email.strip() for email in v.split(",") if email.strip()]

        # Basic email validation for CC addresses
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email in cc_emails:
            if not email_pattern.match(email):
                raise ValueError(f"Invalid email address in CC: {email}")

        return v


class FeedbackValidationErrorSchema(BaseModel):
    """
    Schema for feedback validation errors.
    """

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[str] = Field(None, description="Value that failed validation")

    model_config = ConfigDict(from_attributes=True)


class FeedbackSubmissionResponseSchema(BaseResponseSchema):
    """
    Schema for feedback submission responses.
    """

    status: ResponseStatus = Field(
        ResponseStatus.SUCCESS, description="Response status"
    )
    message: str = Field(..., description="Human-readable response message")
    ticket_id: Optional[str] = Field(None, description="RT ticket ID (if available)")
    submission_id: Optional[str] = Field(None, description="Internal submission ID")

    model_config = ConfigDict(from_attributes=True)


class FeedbackErrorResponseSchema(BaseResponseSchema):
    """
    Schema for feedback error responses.
    """

    status: ResponseStatus = Field(ResponseStatus.ERROR, description="Response status")
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    validation_errors: Optional[List[FeedbackValidationErrorSchema]] = Field(
        None, description="Validation errors if any"
    )
    request_id: Optional[str] = Field(
        None, description="Unique request identifier for tracking"
    )

    model_config = ConfigDict(from_attributes=True)


class FeedbackHealthResponseSchema(BaseResponseSchema):
    """
    Schema for feedback service health check responses.
    """

    status: ResponseStatus = Field(
        ResponseStatus.SUCCESS, description="Response status"
    )
    service: str = Field(..., description="Service name")
    message: str = Field(..., description="Health status message")
    features: Optional[dict] = Field(None, description="Available feedback features")

    model_config = ConfigDict(from_attributes=True)


# Add feedback-specific error codes to the existing ErrorCode enum
# Note: These would need to be added to the main ErrorCode enum in response_schemas.py
class FeedbackErrorCode(str):
    """Feedback-specific error codes."""

    FEEDBACK_SUBMISSION_FAILED = "FEEDBACK_SUBMISSION_FAILED"
    FEEDBACK_VALIDATION_ERROR = "FEEDBACK_VALIDATION_ERROR"
    FEEDBACK_SERVICE_UNAVAILABLE = "FEEDBACK_SERVICE_UNAVAILABLE"
    RT_QUEUE_ERROR = "RT_QUEUE_ERROR"
