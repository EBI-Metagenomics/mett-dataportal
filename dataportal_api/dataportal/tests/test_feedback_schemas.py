import pytest
from pydantic import ValidationError
from dataportal.schema.feedback_schemas import FeedbackSubmissionSchema


class TestFeedbackSubmissionSchema:
    """Test cases for FeedbackSubmissionSchema validation."""

    def test_valid_feedback_submission(self):
        """Test that valid feedback data passes validation."""
        valid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "subject": "Bug Report",
            "feedback": "I found a bug in the genome viewer. The sequence display is not working correctly.",
        }

        feedback = FeedbackSubmissionSchema(**valid_data)
        assert feedback.name == "John Doe"
        assert feedback.email == "john.doe@example.com"
        assert feedback.subject == "Bug Report"
        assert (
            feedback.feedback
            == "I found a bug in the genome viewer. The sequence display is not working correctly."
        )
        assert feedback.cc is None

    def test_valid_feedback_with_cc(self):
        """Test that valid feedback with CC emails passes validation."""
        valid_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "cc": "colleague@example.com,manager@example.com",
            "subject": "Feature Request",
            "feedback": "It would be great to have an export feature for the search results.",
        }

        feedback = FeedbackSubmissionSchema(**valid_data)
        assert feedback.cc == "colleague@example.com,manager@example.com"

    def test_invalid_email(self):
        """Test that invalid email fails validation."""
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "subject": "Test",
            "feedback": "This is a test feedback message.",
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        assert "email" in str(exc_info.value)

    def test_invalid_cc_emails(self):
        """Test that invalid CC emails fail validation."""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "cc": "invalid-email,another-invalid",
            "subject": "Test",
            "feedback": "This is a test feedback message.",
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        assert "cc" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            # Missing subject and feedback
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        errors = exc_info.value.errors()
        assert len(errors) == 2  # subject and feedback missing
        field_names = [error["loc"][0] for error in errors]
        assert "subject" in field_names
        assert "feedback" in field_names

    def test_short_feedback(self):
        """Test that feedback shorter than 10 characters fails validation."""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "subject": "Test",
            "feedback": "Short",  # Less than 10 characters
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        assert "feedback" in str(exc_info.value)

    def test_invalid_name(self):
        """Test that names with invalid characters fail validation."""
        invalid_data = {
            "name": "John123",  # Contains numbers
            "email": "john.doe@example.com",
            "subject": "Test",
            "feedback": "This is a valid feedback message with enough characters.",
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        assert "name" in str(exc_info.value)

    def test_empty_fields(self):
        """Test that empty fields fail validation."""
        invalid_data = {
            "name": "",
            "email": "john.doe@example.com",
            "subject": "",
            "feedback": "This is a valid feedback message.",
        }

        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionSchema(**invalid_data)

        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]
        assert "name" in field_names
        assert "subject" in field_names

    def test_whitespace_only_fields(self):
        """Test that whitespace-only fields are properly handled."""
        valid_data = {
            "name": "  John Doe  ",  # Should be trimmed
            "email": "john.doe@example.com",
            "subject": "  Test Subject  ",  # Should be trimmed
            "feedback": "  This is a valid feedback message.  ",  # Should be trimmed
        }

        feedback = FeedbackSubmissionSchema(**valid_data)
        assert feedback.name == "John Doe"
        assert feedback.subject == "Test Subject"
        assert feedback.feedback == "This is a valid feedback message."
