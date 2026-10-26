"""
Production OpenAI Provider Implementation.
Communicates strictly server-to-server with OpenAI's API.
Ensures zero exposure of API keys, bearer tokens, or internal tracebacks.
"""
import time
import json
import logging
from typing import Optional, Dict, Any, List
from .base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, UsageMetadata
from ..exceptions import (
    AIProviderError,
    AIConfigurationError,
    AIAuthenticationError,
    AIRateLimitError,
    AITimeoutError,
    AIServiceUnavailableError,
)

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    Concrete AI provider wrapping the official OpenAI Python SDK.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ):
        if not api_key or not api_key.strip():
            raise AIConfigurationError(
                "OpenAI API key is missing or blank. Configure OPENAI_API_KEY in backend/.env."
            )
        self.api_key = api_key.strip()
        self.model = model.strip() if model else "gpt-4o-mini"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.api_key,
                timeout=float(self.timeout_seconds),
                max_retries=self.max_retries,
            )
        except Exception as exc:
            # Mask any raw keys from initialization errors
            sanitized_msg = str(exc).replace(self.api_key, "[REDACTED_API_KEY]")
            logger.error("Failed to initialize OpenAI client: %s", sanitized_msg)
            raise AIConfigurationError("Failed to initialize OpenAI client.") from None

    def __repr__(self) -> str:
        # Prevent API key leakage in debugger, string representations, or logs
        return f"<OpenAIProvider model='{self.model}' timeout={self.timeout_seconds}s>"

    def generate_turn(self, request: LLMRequest) -> LLMResponse:
        import openai

        # Build payload messages
        api_messages: List[Dict[str, str]] = []

        # 1. System Prompt + Reference Knowledge
        system_content = request.system_instruction.strip()
        if request.knowledge_chunks:
            system_content += "\n\n--- VERIFIED DOCUMENTATION CONTEXT ---\n"
            for i, chunk in enumerate(request.knowledge_chunks, 1):
                title = chunk.get("source_title", f"Document #{i}")
                section = chunk.get("section_title", "")
                text = chunk.get("content", "").strip()
                system_content += f"\n[Reference {i}: {title} | Section: {section}]\n{text}\n"

        api_messages.append({"role": "system", "content": system_content})

        # 2. Add turn history
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant", "system"):
                api_messages.append({"role": role, "content": content})

        # Configure completion parameters
        create_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        # Optional JSON mode if schema provided
        if request.response_schema:
            create_kwargs["response_format"] = {"type": "json_object"}

        start_time = time.time()
        try:
            completion = self._client.chat.completions.create(**create_kwargs)
        except openai.AuthenticationError:
            logger.warning("OpenAI authentication error (HTTP 401).")
            raise AIAuthenticationError("OpenAI authentication failed. Check configured API credentials.") from None
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit reached (HTTP 429).")
            raise AIRateLimitError("OpenAI rate limit exceeded. Please retry shortly.") from None
        except openai.APITimeoutError:
            logger.warning("OpenAI request timed out after %ds.", self.timeout_seconds)
            raise AITimeoutError(f"OpenAI request timed out after {self.timeout_seconds} seconds.") from None
        except openai.APIConnectionError as exc:
            logger.error("OpenAI connection failed: %s", exc.__class__.__name__)
            raise AIServiceUnavailableError("Failed to connect to OpenAI service.") from None
        except openai.APIStatusError as exc:
            logger.error("OpenAI status error: %s (code: %s)", exc.__class__.__name__, getattr(exc, "status_code", "unknown"))
            raise AIProviderError(f"OpenAI service returned error status {getattr(exc, 'status_code', 500)}.") from None
        except Exception as exc:
            sanitized_msg = str(exc).replace(self.api_key, "[REDACTED_API_KEY]")
            logger.error("Unexpected error in OpenAI completion: %s", sanitized_msg)
            raise AIProviderError("An unexpected error occurred during consultation generation.") from None

        latency_ms = int((time.time() - start_time) * 1000)

        # Parse output and usage
        choice = completion.choices[0]
        raw_text = choice.message.content or ""
        extracted_profile = {}

        if request.response_schema:
            try:
                parsed_json = json.loads(raw_text)
                if isinstance(parsed_json, dict):
                    extracted_profile = parsed_json.get("extracted_profile", {})
                    # If model returned pure profile or wrapped text
                    if "answer" in parsed_json:
                        raw_text = parsed_json["answer"]
                    elif "content" in parsed_json:
                        raw_text = parsed_json["content"]
            except Exception:
                # Fallback to raw text if JSON parsing fails
                pass

        # Parse usage metadata
        usage_data = getattr(completion, "usage", None)
        prompt_tokens = getattr(usage_data, "prompt_tokens", 0) if usage_data else 0
        completion_tokens = getattr(usage_data, "completion_tokens", 0) if usage_data else 0
        total_tokens = getattr(usage_data, "total_tokens", 0) if usage_data else (prompt_tokens + completion_tokens)

        # Build citations from referenced knowledge chunks
        citations = []
        for i, chunk in enumerate(request.knowledge_chunks):
            citations.append({
                "source_title": chunk.get("source_title", f"Document #{i+1}"),
                "source_url": chunk.get("source_url", ""),
                "excerpt": chunk.get("content", "")[:120],
            })

        usage = UsageMetadata(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            model=getattr(completion, "model", self.model),
        )

        return LLMResponse(
            content=raw_text,
            extracted_profile=extracted_profile,
            citations=citations,
            usage=usage,
            raw_model_id=getattr(completion, "model", self.model),
        )
