"""
Structured logging utilities for VigilancePilot.
"""

import logging
import sys
from typing import Any, Optional
import structlog
from structlog.types import FilteringBoundLogger


def setup_logging(debug: bool = False, json_logs: bool = False) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        debug: Enable debug logging
        json_logs: Output logs in JSON format
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_logs:
        # JSON output for production
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ])
    else:
        # Pretty console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Example:
        with LogContext(request_id="123", user_id="456"):
            logger.info("processing request")
    """
    
    def __init__(self, **kwargs: Any):
        """
        Initialize log context.
        
        Args:
            **kwargs: Key-value pairs to add to log context
        """
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        """Enter context."""
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if self.token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


def log_function_call(logger: FilteringBoundLogger):
    """
    Decorator to log function calls with arguments and results.
    
    Args:
        logger: Logger instance to use
        
    Example:
        @log_function_call(logger)
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                "calling function",
                function=func.__name__,
                args=args,
                kwargs=kwargs
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    "function completed",
                    function=func.__name__,
                    result=result
                )
                return result
            except Exception as e:
                logger.error(
                    "function failed",
                    function=func.__name__,
                    error=str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def sanitize_log_data(data: Any, sensitive_keys: Optional[list] = None) -> Any:
    """
    Sanitize sensitive data from log output.
    
    Args:
        data: Data to sanitize
        sensitive_keys: List of keys to redact (default: common sensitive keys)
        
    Returns:
        Sanitized data
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password", "token", "api_key", "secret", "auth",
            "authorization", "apikey", "api-key", "access_token"
        ]
    
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if k.lower() in [s.lower() for s in sensitive_keys]
            else sanitize_log_data(v, sensitive_keys)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_log_data(item, sensitive_keys) for item in data]
    else:
        return data
