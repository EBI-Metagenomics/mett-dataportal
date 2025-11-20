import logging
from datetime import datetime
from django.middleware.common import MiddlewareMixin

from dataportal.middleware.swagger_templates import (
    HEADER_HTML,
    FOOTER_HTML,
    HEADER_CSS_JS,
    BREADCRUMB_HTML,
)

logger = logging.getLogger(__name__)


class RemoveCOOPHeaderMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Remove the Cross-Origin-Opener-Policy header if it exists
        if "Cross-Origin-Opener-Policy" in response:
            del response["Cross-Origin-Opener-Policy"]
        return response


class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log the request details
        start_time = datetime.now()
        request.start_time = start_time
        logger.info(f"API accessed: {request.method} {request.get_full_path()} at {start_time}")

    def process_response(self, request, response):
        # Log the response details
        end_time = datetime.now()
        start_time = getattr(request, "start_time", None)
        if start_time:
            duration = end_time - start_time
        else:
            duration = "unknown"

        logger.info(
            f"API response: {response.status_code} {request.get_full_path()} took {duration}"
        )
        return response


class SwaggerHeaderFooterMiddleware(MiddlewareMixin):
    """
    Middleware that injects Data Portal header and footer into Swagger UI pages.
    This wraps django-ninja's default Swagger HTML with our header/footer.
    """

    def process_response(self, request, response):
        # Only process HTML responses for Swagger docs
        if request.path.startswith("/api/docs") and response.get("Content-Type", "").startswith(
            "text/html"
        ):
            try:
                content = response.content.decode("utf-8")

                # Inject CSS/JS in head (before closing </head>)
                if "</head>" in content and "assets.emblstatic.net/vf" not in content:
                    content = content.replace("</head>", f"{HEADER_CSS_JS}</head>")

                # Inject header after opening <body> tag
                if "<body" in content and "masthead-black-bar" not in content:
                    # Find the body tag and inject header after it
                    body_match = content.find("<body")
                    if body_match != -1:
                        # Find the closing > of body tag
                        body_end = content.find(">", body_match) + 1
                        # Inject header and breadcrumb
                        content = (
                            content[:body_end]
                            + "\n"
                            + HEADER_HTML
                            + "\n"
                            + BREADCRUMB_HTML
                            + content[body_end:]
                        )

                # Inject footer before closing </body>
                if "</body>" in content and "vf-footer" not in content:
                    content = content.replace("</body>", f"{FOOTER_HTML}</body>")

                response.content = content.encode("utf-8")
            except (UnicodeDecodeError, AttributeError, Exception) as e:
                # If content is not text or can't be decoded, skip injection
                logger.warning(f"Failed to inject header/footer into Swagger page: {e}")
                pass

        return response
