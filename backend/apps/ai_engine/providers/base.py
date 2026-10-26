"""
Abstract Base Provider for AI Consultation Models.
"""
from abc import ABC, abstractmethod
from ..types import LLMRequest, LLMResponse

class BaseLLMProvider(ABC):
    """
    Vendor-agnostic interface for AI consultation generation.
    Any concrete provider (OpenAI, Gemini, Ollama, Mock) must implement this interface.
    """

    @abstractmethod
    def generate_turn(self, request: LLMRequest) -> LLMResponse:
        """
        Execute a single consultation turn.
        Must return normalized LLMResponse or raise a normalized AIProviderError subclass.
        """
        pass
