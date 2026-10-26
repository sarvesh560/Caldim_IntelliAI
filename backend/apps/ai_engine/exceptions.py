"""
Normalized exception hierarchy for the AI engine.
Shields application views and services from vendor-specific SDK errors,
ensuring zero leak of credentials, bearer tokens, or internal tracebacks.
"""

class AIProviderError(Exception):
    """Base exception for all AI provider failures."""
    def __init__(self, message: str, code: str = "provider_error"):
        super().__init__(message)
        self.message = message
        self.code = code

class AIConfigurationError(AIProviderError):
    """Raised when provider configuration or API keys are missing/invalid."""
    def __init__(self, message: str):
        super().__init__(message, code="configuration_error")

class AIAuthenticationError(AIProviderError):
    """Raised when the provider rejects credentials (HTTP 401)."""
    def __init__(self, message: str = "Authentication with AI provider failed."):
        super().__init__(message, code="authentication_error")

class AIRateLimitError(AIProviderError):
    """Raised when upstream AI provider rate limits are exceeded (HTTP 429)."""
    def __init__(self, message: str = "AI provider rate limit exceeded. Please retry shortly."):
        super().__init__(message, code="rate_limit_error")

class AITimeoutError(AIProviderError):
    """Raised when an AI provider request exceeds the configured timeout."""
    def __init__(self, message: str = "AI provider request timed out."):
        super().__init__(message, code="timeout_error")

class AIServiceUnavailableError(AIProviderError):
    """Raised when upstream AI service experiences downtime or network errors (HTTP 500/503)."""
    def __init__(self, message: str = "AI service is temporarily unavailable."):
        super().__init__(message, code="service_unavailable")

class AIContentFilterError(AIProviderError):
    """Raised when input/output triggers provider safety or content moderation."""
    def __init__(self, message: str = "Content flagged by provider safety filters."):
        super().__init__(message, code="content_filter_error")
