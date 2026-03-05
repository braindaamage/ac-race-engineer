"""Error handling public API."""

from api.errors.handlers import register_error_handlers
from api.errors.models import ErrorDetail, ErrorResponse

__all__ = ["ErrorDetail", "ErrorResponse", "register_error_handlers"]
