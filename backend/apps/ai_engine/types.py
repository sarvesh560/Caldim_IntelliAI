"""
Normalized data types for provider-independent AI consultation requests and responses.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class UsageMetadata:
    """Normalized token and timing telemetry."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    model: str = ""

@dataclass
class LLMRequest:
    """
    Vendor-agnostic consultation turn request.
    Encapsulates system instructions, conversation history, and optional RAG context chunks.
    """
    system_instruction: str
    messages: List[Dict[str, str]]
    knowledge_chunks: List[Dict[str, str]] = field(default_factory=list)
    response_schema: Optional[Dict[str, Any]] = None
    temperature: float = 0.2
    max_tokens: int = 1200

@dataclass
class LLMResponse:
    """
    Normalized response returned by any AI provider.
    """
    content: str
    extracted_profile: Dict[str, Any] = field(default_factory=dict)
    citations: List[Dict[str, str]] = field(default_factory=list)
    usage: UsageMetadata = field(default_factory=UsageMetadata)
    raw_model_id: str = ""
