import logging
import uuid
from typing import Dict, Any

from ..schema.feedback_schemas import FeedbackSubmissionSchema

logger = logging.getLogger(__name__)


class FeedbackService:

    @staticmethod
    def submit_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:

        submission_id = str(uuid.uuid4())

        try:
            logger.info(
                f"Feedback submission {submission_id} received from {feedback_data.get('name', 'Unknown')}: {feedback_data.get('subject', 'No subject')}"
            )
            logger.info(
                f"Feedback details: {feedback_data.get('feedback', 'No details')}"
            )

            # TODO: RT queue system configuration
            # rt_client = RTClient(settings.RT_SERVER_URL, settings.RT_USERNAME, settings.RT_PASSWORD)
            # ticket_data = {
            #     'Subject': feedback_data['subject'],
            #     'Content': f"Name: {feedback_data['name']}\nEmail: {feedback_data['email']}\nCC: {feedback_data.get('cc', '')}\n\nFeedback:\n{feedback_data['feedback']}",
            #     'Queue': settings.RT_FEEDBACK_QUEUE,
            #     'Requestor': feedback_data['email']
            # }
            # if feedback_data.get('cc'):
            #     ticket_data['Cc'] = feedback_data['cc']
            #
            # ticket_id = rt_client.create_ticket(ticket_data)

            return {
                "success": True,
                "message": "Feedback submitted successfully. We will review it shortly.",
                "ticket_id": None,  # Will be populated when RT integration is complete
                "submission_id": submission_id,
            }

        except Exception as e:
            logger.error(f"Error submitting feedback {submission_id}: {str(e)}")
            return {
                "success": False,
                "message": "Failed to submit feedback. Please try again or contact us directly.",
                "error": str(e),
                "submission_id": submission_id,
            }

    @staticmethod
    def validate_feedback_data(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated_data = FeedbackSubmissionSchema(**feedback_data)
            return {"valid": True, "data": validated_data.model_dump()}
        except Exception as e:
            return {"valid": False, "errors": [str(e)]}
