"""
Deterministic Mock AI Provider for automated testing and CI pipelines.
Consumes zero network calls, zero billing credits, and guarantees reproducible outputs.
"""
import time
from typing import Optional, Dict, Any
from .base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, UsageMetadata
from ..exceptions import (
    AITimeoutError,
    AIAuthenticationError,
    AIRateLimitError,
    AIServiceUnavailableError,
)

DEFAULT_STRUCTURED_MOCK_RESPONSE = """{
  "reply": "Based on our operational architecture evaluation, your plant operations exhibit significant spreadsheet synchronization friction between daily task allocation and month-end payroll execution. We have structured a root-cause breakdown and recommended an operational roadmap.",
  "analysis": {
    "root_causes": ["Manual dual-entry timesheet aggregation", "Fragmented leave reconciliation across separate shift rosters"],
    "operational_friction": ["5-day month-end payroll calculation turnaround", "Spreadsheet transposition risk"],
    "compliance_or_accuracy_risks": ["PF / ESI deduction calculation latency", "Overtime wage discrepancy"]
  },
  "recommendations": [
    {
      "product_name": "CALTIMS HR & Payroll Engine",
      "product_slug": "caltims",
      "suitability_rationale": "Directly synchronizes timesheet grids to automated payroll runs without manual recalculation.",
      "source_url": "https://caldimproducts.com/products/caltims",
      "verified": false
    }
  ],
  "solution_comparison": {
    "primary_solution": "Direct timesheet-to-payroll automation with role-based access",
    "alternative_approach": "Manual Excel template consolidation with macro scripting",
    "tradeoff_analysis": "Automation eliminates 3-5 days of monthly manual entry and audit vulnerabilities, but requires initial shift roster master configuration."
  },
  "dynamic_questions": [
    "What is your total active headcount across production shifts?",
    "Which banking portal or host-to-host payment protocol does your finance team require for monthly salary disbursements?",
    "Do you operate on fixed 8-hour shift rotations or dynamic overtime calculations?"
  ],
  "assumptions_and_limitations": [
    "Assumes employee master records are centrally maintained in an active database.",
    "Hardware biometric integration requires on-site network connectivity."
  ],
  "next_steps": [
    "Step 1: Export current shift roster and leave policy templates for validation.",
    "Step 2: Request preview demonstration access from CALDIM Software Division.",
    "Step 3: Benchmark timesheet grid submission with a pilot cohort of 25 workers."
  ],
  "visual_spec": {
    "diagram_type": "workflow",
    "title": "CALTIMS Operational Workflow Architecture",
    "steps": [
      "1. Shift Scheduling & Time Log Entry",
      "2. Automated Leave & OT Reconciliation",
      "3. Tax Slab & Statutory Deduction Engine",
      "4. Bank Disbursement Export & Direct Audit Trail"
    ]
  }
}"""


class MockLLMProvider(BaseLLMProvider):
    """
    Mock AI Provider for isolated unit and integration testing.
    """

    def __init__(
        self,
        canned_response: Optional[str] = None,
        extracted_profile: Optional[Dict[str, Any]] = None,
        simulate_error: Optional[str] = None,
    ):
        self.canned_response = canned_response if canned_response is not None else DEFAULT_STRUCTURED_MOCK_RESPONSE
        self.extracted_profile = extracted_profile or {}
        self.simulate_error = simulate_error
        self.call_history = []

    def generate_turn(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        self.call_history.append(request)

        # Emulate error scenarios on demand
        if self.simulate_error == "timeout":
            raise AITimeoutError("Simulated mock timeout.")
        elif self.simulate_error == "auth":
            raise AIAuthenticationError("Simulated mock authentication rejection.")
        elif self.simulate_error == "ratelimit":
            raise AIRateLimitError("Simulated mock rate limit exceeded.")
        elif self.simulate_error == "unavailable":
            raise AIServiceUnavailableError("Simulated mock service downtime.")

        # Build citations if knowledge chunks were passed in request
        citations = []
        for i, chunk in enumerate(request.knowledge_chunks):
            citations.append({
                "source_title": chunk.get("source_title", f"Document #{i+1}"),
                "source_url": chunk.get("source_url", ""),
                "excerpt": chunk.get("content", "")[:120],
            })

        # Calculate mock token usage
        prompt_chars = len(request.system_instruction) + sum(len(m.get("content", "")) for m in request.messages)
        prompt_tokens = max(1, prompt_chars // 4)
        completion_tokens = max(1, len(self.canned_response) // 4)
        latency_ms = int((time.time() - start_time) * 1000)

        usage = UsageMetadata(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            model="mock-consultant-v1",
        )

        return LLMResponse(
            content=self.canned_response,
            extracted_profile=self.extracted_profile,
            citations=citations,
            usage=usage,
            raw_model_id="mock-consultant-v1",
        )
