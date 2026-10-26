"""
AI Provider Factory.
Instantiates the configured provider based on Django settings.
Explicitly prohibits silent mock fallback in production.
"""
import logging
from django.conf import settings
from .base import BaseLLMProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider
from ..exceptions import AIConfigurationError

logger = logging.getLogger(__name__)

def get_ai_provider() -> BaseLLMProvider:
    """
    Factory function to retrieve active AI provider instance.

    Guarantees:
    - In test environments with AI_PROVIDER='mock', returns isolated MockLLMProvider.
    - When AI_PROVIDER='openai', instantiates OpenAIProvider with configured backend settings.
    - If credentials are missing or provider fails, raises an explicit AIConfigurationError;
      NEVER silently switches to a mock provider or fabricates responses in production.
    """
    provider_name = getattr(settings, "AI_PROVIDER", "openai").strip().lower()

    if provider_name == "mock":
        return MockLLMProvider()

    if provider_name == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "").strip()
        if not api_key:
            raise AIConfigurationError(
                "OPENAI_API_KEY is not configured in backend environment. "
                "Add your valid key to backend/.env."
            )
        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini").strip()
        timeout = getattr(settings, "AI_REQUEST_TIMEOUT_SECONDS", 30)
        retries = getattr(settings, "AI_MAX_RETRIES", 1)

        return OpenAIProvider(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout,
            max_retries=retries,
        )

    raise AIConfigurationError(
        f"Unsupported AI_PROVIDER '{provider_name}'. Supported options are 'openai' and 'mock'."
    )
