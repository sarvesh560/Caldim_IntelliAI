"""
Unit and Integration Tests for AI Consultation Engine (apps.ai_engine).
Executes entirely with isolated mock providers; consumes ZERO network calls or API credits.
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
from django.core.management import call_command
from io import StringIO

from apps.ai_engine.types import LLMRequest, LLMResponse, UsageMetadata
from apps.ai_engine.exceptions import (
    AIProviderError,
    AIConfigurationError,
    AIAuthenticationError,
    AIRateLimitError,
    AITimeoutError,
    AIServiceUnavailableError,
)
from apps.ai_engine.providers.base import BaseLLMProvider
from apps.ai_engine.providers.mock_provider import MockLLMProvider
from apps.ai_engine.providers.openai_provider import OpenAIProvider
from apps.ai_engine.providers.factory import get_ai_provider

class MockProviderTests(TestCase):
    """Test the deterministic Mock AI Provider."""

    def test_mock_provider_generation(self):
        provider = MockLLMProvider(
            canned_response="CalTIMS calculates payroll automatically.",
            extracted_profile={"industry": "Manufacturing"},
        )
        req = LLMRequest(
            system_instruction="You are a consultation AI.",
            messages=[{"role": "user", "content": "Tell me about CalTIMS"}],
            knowledge_chunks=[{
                "source_title": "CalTIMS Doc",
                "source_url": "https://caldimproducts.com/products/caltims",
                "content": "CalTIMS bridges timesheets to payroll."
            }],
        )
        res = provider.generate_turn(req)

        self.assertIsInstance(res, LLMResponse)
        self.assertEqual(res.content, "CalTIMS calculates payroll automatically.")
        self.assertEqual(res.extracted_profile["industry"], "Manufacturing")
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0]["source_title"], "CalTIMS Doc")
        self.assertGreater(res.usage.total_tokens, 0)
        self.assertEqual(len(provider.call_history), 1)

    def test_mock_provider_simulated_errors(self):
        req = LLMRequest(system_instruction="sys", messages=[])

        timeout_provider = MockLLMProvider(simulate_error="timeout")
        with self.assertRaises(AITimeoutError):
            timeout_provider.generate_turn(req)

        auth_provider = MockLLMProvider(simulate_error="auth")
        with self.assertRaises(AIAuthenticationError):
            auth_provider.generate_turn(req)

        rate_provider = MockLLMProvider(simulate_error="ratelimit")
        with self.assertRaises(AIRateLimitError):
            rate_provider.generate_turn(req)

        down_provider = MockLLMProvider(simulate_error="unavailable")
        with self.assertRaises(AIServiceUnavailableError):
            down_provider.generate_turn(req)

class ProviderFactoryTests(TestCase):
    """Test AI Provider Factory behavior and isolation."""

    @override_settings(AI_PROVIDER="mock")
    def test_factory_returns_mock_provider(self):
        provider = get_ai_provider()
        self.assertIsInstance(provider, MockLLMProvider)

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="")
    def test_factory_raises_when_openai_key_missing(self):
        with self.assertRaises(AIConfigurationError) as ctx:
            get_ai_provider()
        self.assertIn("OPENAI_API_KEY is not configured", str(ctx.exception))

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="sk-dummy-test-key", OPENAI_MODEL="gpt-4o-mini")
    def test_factory_returns_openai_provider_when_configured(self):
        provider = get_ai_provider()
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.model, "gpt-4o-mini")

    @override_settings(AI_PROVIDER="unsupported_vendor")
    def test_factory_rejects_unsupported_provider(self):
        with self.assertRaises(AIConfigurationError) as ctx:
            get_ai_provider()
        self.assertIn("Unsupported AI_PROVIDER", str(ctx.exception))

class OpenAIProviderTests(TestCase):
    """Test OpenAIProvider client wrapper with mocked OpenAI SDK."""

    def test_openai_provider_rejects_empty_key(self):
        with self.assertRaises(AIConfigurationError):
            OpenAIProvider(api_key="")

    def test_openai_provider_repr_does_not_leak_key(self):
        dummy_secret = "sk-proj-super-secret-key-123456789"
        provider = OpenAIProvider(api_key=dummy_secret, model="gpt-4o-mini")
        repr_str = repr(provider)
        self.assertNotIn(dummy_secret, repr_str)
        self.assertIn("gpt-4o-mini", repr_str)

    @patch("openai.OpenAI")
    def test_openai_provider_successful_turn(self, mock_openai_cls):
        # Setup mock OpenAI client response
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "CalTIMS automates payroll."
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_completion.model = "gpt-4o-mini"
        mock_completion.usage.prompt_tokens = 50
        mock_completion.usage.completion_tokens = 20
        mock_completion.usage.total_tokens = 70
        mock_client.chat.completions.create.return_value = mock_completion

        provider = OpenAIProvider(api_key="sk-fake-key", model="gpt-4o-mini")
        req = LLMRequest(
            system_instruction="System prompt",
            messages=[{"role": "user", "content": "Question"}],
        )
        res = provider.generate_turn(req)

        self.assertEqual(res.content, "CalTIMS automates payroll.")
        self.assertEqual(res.usage.prompt_tokens, 50)
        self.assertEqual(res.usage.completion_tokens, 20)
        self.assertEqual(res.usage.total_tokens, 70)
        self.assertEqual(res.raw_model_id, "gpt-4o-mini")

    @patch("openai.OpenAI")
    def test_openai_provider_structured_json_parsing(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"answer": "Understood.", "extracted_profile": {"company_name": "Apex Machinery"}}'
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_completion.usage = None
        mock_client.chat.completions.create.return_value = mock_completion

        provider = OpenAIProvider(api_key="sk-fake-key", model="gpt-4o-mini")
        req = LLMRequest(
            system_instruction="System prompt",
            messages=[{"role": "user", "content": "My company is Apex Machinery"}],
            response_schema={"type": "object"},
        )
        res = provider.generate_turn(req)

        self.assertEqual(res.content, "Understood.")
        self.assertEqual(res.extracted_profile["company_name"], "Apex Machinery")

    @patch("openai.OpenAI")
    def test_openai_provider_exception_translation(self, mock_openai_cls):
        import openai

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        provider = OpenAIProvider(api_key="sk-fake-key", model="gpt-4o-mini")
        req = LLMRequest(system_instruction="sys", messages=[])

        # 1. Authentication Error
        mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
            message="Invalid API Key", response=MagicMock(status_code=401), body=None
        )
        with self.assertRaises(AIAuthenticationError):
            provider.generate_turn(req)

        # 2. Rate Limit Error
        mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            message="Rate limit exceeded", response=MagicMock(status_code=429), body=None
        )
        with self.assertRaises(AIRateLimitError):
            provider.generate_turn(req)

        # 3. Timeout Error
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(request=MagicMock())
        with self.assertRaises(AITimeoutError):
            provider.generate_turn(req)

        # 4. Connection Error
        mock_client.chat.completions.create.side_effect = openai.APIConnectionError(request=MagicMock())
        with self.assertRaises(AIServiceUnavailableError):
            provider.generate_turn(req)

class VerifyAIProviderCommandTests(TestCase):
    """Test the management command verify_ai_provider without live network requests."""

    @override_settings(AI_PROVIDER="mock")
    def test_command_succeeds_on_mock_provider(self):
        out = StringIO()
        call_command("verify_ai_provider", stdout=out)
        output = out.getvalue()
        self.assertIn("Mock AI Provider is active", output)

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="")
    def test_command_fails_safely_when_key_empty(self):
        out = StringIO()
        with self.assertRaises(SystemExit) as cm:
            call_command("verify_ai_provider", stdout=out)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("OPENAI_API_KEY is missing or empty", out.getvalue())

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="sk-dummy-test-key", OPENAI_MODEL="gpt-4o-mini")
    @patch("openai.OpenAI")
    def test_command_verifies_model_catalogue(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_model = MagicMock()
        mock_model.id = "gpt-4o-mini"
        mock_client.models.retrieve.return_value = mock_model

        out = StringIO()
        call_command("verify_ai_provider", stdout=out)
        output = out.getvalue()
        self.assertIn("[SUCCESS] OpenAI API connection verified", output)
        self.assertIn("gpt-4o-mini", output)
        # Ensure dummy key was NOT printed
        self.assertNotIn("sk-dummy-test-key", output)


class ConsultationWorkflowIntegrationTests(TestCase):
    """
    Validates end-to-end multi-turn consultation workflow:
    1. Visitor authentication & ownership isolation.
    2. Initial challenge submission and structured response parsing.
    3. Multi-turn conversation state accumulation.
    4. Client message idempotency.
    5. Provider error resilience.
    """

    def setUp(self):
        from rest_framework.test import APIClient
        from apps.visitors.models import Visitor, ConsentCategory, ConsentStatus
        import secrets

        self.client = APIClient()

        # Create Visitor A
        self.raw_token_a = secrets.token_urlsafe(32)
        self.visitor_a = Visitor.objects.create(
            display_name="Elena Vance",
            email="elena.vance@vance-precision.example.com",
            phone="+1-555-019-8833",
            profession="VP of Manufacturing Technology",
            company_name="Vance Precision Industries",
            industry="Precision Machining & Aerospace",
            department="Operations Engineering",
            responsibilities="Overseeing CNC machining and factory telemetry",
        )
        self.visitor_a.set_access_token(self.raw_token_a)
        self.visitor_a.update_completion_status()
        self.visitor_a.save()
        self.visitor_a.consents.create(
            category=ConsentCategory.ESSENTIAL,
            status=ConsentStatus.GRANTED,
        )

        # Create Visitor B (for isolation testing)
        self.raw_token_b = secrets.token_urlsafe(32)
        self.visitor_b = Visitor.objects.create(
            display_name="Marcus Thorne",
            email="marcus.thorne@thorne-logistics.example.com",
            phone="+1-555-019-9944",
            profession="Head of Logistics",
            company_name="Thorne Distribution Corp",
            industry="Supply Chain & Warehousing",
            department="Fulfillment",
            responsibilities="Fleet tracking and warehouse management",
        )
        self.visitor_b.set_access_token(self.raw_token_b)
        self.visitor_b.update_completion_status()
        self.visitor_b.save()
        self.visitor_b.consents.create(
            category=ConsentCategory.ESSENTIAL,
            status=ConsentStatus.GRANTED,
        )

    def test_visitor_authentication_required(self):
        """Unauthenticated requests to consultation endpoints return 401."""
        res_list = self.client.get("/api/v1/consultations/")
        self.assertEqual(res_list.status_code, 401)

        res_post = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "How do we reduce shift overtime errors?"},
            format="json",
        )
        self.assertEqual(res_post.status_code, 401)

    def test_invalid_or_expired_token_rejected(self):
        """Invalid or revoked tokens are rejected with 403."""
        res = self.client.get(
            "/api/v1/consultations/",
            HTTP_X_VISITOR_TOKEN="invalid-fake-token-12345",
        )
        self.assertEqual(res.status_code, 403)

    def test_start_consultation_creates_conversation_and_initial_turn(self):
        """Visitor starts consultation challenge; returns conversation with structured analysis."""
        payload = {
            "title": "Timesheet & Payroll Bottleneck",
            "initial_message": "We have 350 machine operators across three plants. Calculating weekly payroll from spreadsheet logs takes our team 4 days.",
            "client_message_id": "msg-client-init-001",
        }
        res = self.client.post(
            "/api/v1/consultations/",
            payload,
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["visitor_id"], str(self.visitor_a.id))
        self.assertEqual(data["title"], "Timesheet & Payroll Bottleneck")
        self.assertEqual(len(data["messages"]), 2)

        user_msg = data["messages"][0]
        self.assertEqual(user_msg["role"], "user")
        self.assertEqual(user_msg["client_message_id"], "msg-client-init-001")

        assistant_msg = data["messages"][1]
        self.assertEqual(assistant_msg["role"], "assistant")
        payload_data = assistant_msg["structured_payload"]
        self.assertIn("analysis", payload_data)
        self.assertIn("dynamic_questions", payload_data)
        self.assertIn("next_steps", payload_data)
        self.assertGreater(len(payload_data["dynamic_questions"]), 0)

    def test_multi_turn_consultation_accumulates_state(self):
        """Follow-up turns append messages and update conversation consultation state."""
        # 1. Start consultation
        init_res = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "Our plant shift workers struggle with manual overtime logging."},
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(init_res.status_code, 201)
        conv_id = init_res.json()["id"]

        # 2. Submit follow-up turn
        follow_up_payload = {
            "content": "We run three 8-hour shift rotations and need automated statutory PF/ESI calculations.",
            "client_message_id": "msg-followup-002",
        }
        turn_res = self.client.post(
            f"/api/v1/consultations/{conv_id}/messages/",
            follow_up_payload,
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(turn_res.status_code, 200)
        turn_data = turn_res.json()
        self.assertEqual(turn_data["conversation_id"], conv_id)
        self.assertIn("consultation_state", turn_data)

        # 3. Verify complete conversation history has 4 messages
        detail_res = self.client.get(
            f"/api/v1/consultations/{conv_id}/",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(detail_res.status_code, 200)
        messages = detail_res.json()["messages"]
        self.assertEqual(len(messages), 4)

    def test_conversation_ownership_isolation(self):
        """Visitor B cannot retrieve or post messages to Visitor A's conversation."""
        # Visitor A creates conversation
        res_a = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "Confidential Vance plant challenge."},
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        conv_a_id = res_a.json()["id"]

        # Visitor B attempts to retrieve Visitor A's conversation -> 404 Not Found
        res_b_get = self.client.get(
            f"/api/v1/consultations/{conv_a_id}/",
            HTTP_X_VISITOR_TOKEN=self.raw_token_b,
        )
        self.assertEqual(res_b_get.status_code, 404)

        # Visitor B attempts to append a message to Visitor A's conversation -> 404 Not Found
        res_b_post = self.client.post(
            f"/api/v1/consultations/{conv_a_id}/messages/",
            {"content": "Unauthorized injection attempt."},
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_b,
        )
        self.assertEqual(res_b_post.status_code, 404)

    def test_client_message_idempotency(self):
        """Retrying message submission with same client_message_id returns existing turn."""
        from apps.ai_engine.models import Conversation, ConsultationMessage

        # Start conversation
        res = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "Initial challenge for idempotency."},
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        conv_id = res.json()["id"]

        # First turn
        payload = {"content": "Network retry test", "client_message_id": "client-uuid-12345"}
        turn_1 = self.client.post(
            f"/api/v1/consultations/{conv_id}/messages/",
            payload,
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(turn_1.status_code, 200)
        turn_1_msg_id = turn_1.json()["assistant_message"]["id"]

        # Duplicate turn with same client_message_id
        turn_2 = self.client.post(
            f"/api/v1/consultations/{conv_id}/messages/",
            payload,
            format="json",
            HTTP_X_VISITOR_TOKEN=self.raw_token_a,
        )
        self.assertEqual(turn_2.status_code, 200)
        turn_2_msg_id = turn_2.json()["assistant_message"]["id"]

        # Must return identical assistant message without duplicate generation
        self.assertEqual(turn_1_msg_id, turn_2_msg_id)
        conv = Conversation.objects.get(id=conv_id)
        # 1 user + 1 assistant (init) + 1 user + 1 assistant (turn) = 4 total messages
        self.assertEqual(conv.messages.count(), 4)

    def test_consultation_blocked_if_onboarding_incomplete(self):
        """Incomplete visitor profile cannot initiate consultation; returns 403 ONBOARDING_INCOMPLETE."""
        from apps.visitors.models import Visitor, ConsentCategory, ConsentStatus
        import secrets

        raw_tok = secrets.token_urlsafe(32)
        incomplete_visitor = Visitor.objects.create(
            display_name="Incomplete Guest",
            # missing email, phone, company, industry
        )
        incomplete_visitor.set_access_token(raw_tok)
        incomplete_visitor.save()
        incomplete_visitor.consents.create(
            category=ConsentCategory.ESSENTIAL,
            status=ConsentStatus.GRANTED,
        )

        res = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "Premature consultation attempt."},
            format="json",
            HTTP_X_VISITOR_TOKEN=raw_tok,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get("code"), "ONBOARDING_INCOMPLETE")

    def test_consultation_blocked_if_essential_consent_missing(self):
        """Visitor without active essential consent cannot initiate consultation; returns 403 CONSENT_REQUIRED."""
        from apps.visitors.models import Visitor
        import secrets

        raw_tok = secrets.token_urlsafe(32)
        no_consent_visitor = Visitor.objects.create(
            display_name="Consented Guest",
            email="guest@example.com",
            phone="+1-555-010-9988",
            profession="CTO",
            company_name="Guest Corp",
            industry="Software",
            department="Engineering",
            responsibilities="Architecture",
        )
        no_consent_visitor.set_access_token(raw_tok)
        no_consent_visitor.update_completion_status()
        no_consent_visitor.save()
        # No essential consent created

        res = self.client.post(
            "/api/v1/consultations/",
            {"initial_message": "Consent missing attempt."},
            format="json",
            HTTP_X_VISITOR_TOKEN=raw_tok,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get("code"), "CONSENT_REQUIRED")


class ProfessionContextTests(TestCase):
    """Test profession categorization, cognitive directives, and alias mapping."""

    def test_resolve_category_all_twelve_domains(self):
        from apps.ai_engine.services.profession_context import ProfessionContextService, ProfessionCategory

        test_cases = [
            ("Textile Production Manager", "production_manufacturing"),
            ("Plant Factory Supervisor", "production_manufacturing"),
            ("Lead Reliability & Maintenance Engineer", "maintenance_reliability"),
            ("Electrical Breakdown Technician", "maintenance_reliability"),
            ("QA / QC Compliance Inspector", "quality_assurance"),
            ("Senior Six Sigma Lead", "quality_assurance"),
            ("Continuous Improvement & Process Engineer", "industrial_process"),
            ("Lead Kaizen Specialist", "industrial_process"),
            ("Senior Backend Software Engineer", "software_it"),
            ("DevOps Cloud Architect", "software_it"),
            ("Founder and Business Owner", "business_leadership"),
            ("Managing Director & CEO", "business_leadership"),
            ("Corporate Finance Manager", "finance_accounting"),
            ("Chief Financial Officer", "finance_accounting"),
            ("VP of Human Resources & Payroll", "hr_workforce"),
            ("Talent Acquisition Manager", "hr_workforce"),
            ("Enterprise Sales Director", "sales_marketing"),
            ("Customer Success & Revenue Lead", "sales_marketing"),
            ("Supply Chain & Logistics Dispatcher", "supply_chain_logistics"),
            ("Warehouse Inventory Controller", "supply_chain_logistics"),
            ("Management Consultant & Advisor", "consultant_researcher"),
            ("Graduate Research Student", "consultant_researcher"),
            ("Astrobiologist", "general_professional"),  # Unknown role falls back cleanly
        ]

        for title, expected_cat in test_cases:
            cat = ProfessionContextService.resolve_category(title)
            self.assertEqual(cat, expected_cat, f"Failed resolving '{title}' -> expected '{expected_cat}', got '{cat}'")

    def test_build_profession_prompt_directives_production_manager(self):
        from apps.ai_engine.services.profession_context import ProfessionContextService

        directives = ProfessionContextService.build_profession_prompt_directives(
            profession="Production Manager",
            industry="Textile Manufacturing",
            department="Weaving & Spinning",
            responsibilities="Managing loom line availability and shift target OEE",
            company_name="Vance Textiles Ltd",
        )
        self.assertIn("Production & Manufacturing Management", directives)
        self.assertIn("Overall Equipment Effectiveness (OEE)", directives)
        self.assertIn("Takt Time & Cycle Time", directives)
        self.assertIn("Vance Textiles Ltd", directives)
        self.assertIn("Textile Manufacturing", directives)

    def test_build_profession_prompt_directives_fallback(self):
        from apps.ai_engine.services.profession_context import ProfessionContextService

        directives = ProfessionContextService.build_profession_prompt_directives(
            profession="",
            industry="",
        )
        self.assertIn("Enterprise & Industrial Professional", directives)
        self.assertIn("Operational Efficiency", directives)


class ProfessionAwareOrchestrationTests(TestCase):
    """Test profession context construction, prompt injection, and dynamic adaptation during orchestration."""

    def setUp(self):
        from apps.visitors.models import Visitor, ConsentCategory, ConsentStatus
        import secrets

        self.token = secrets.token_urlsafe(32)
        self.visitor = Visitor.objects.create(
            display_name="Marcus Vance",
            email="marcus.vance@textiles.example.com",
            profession="Textile Production Manager",
            company_name="Apex Weaving Mills",
            industry="Textile Manufacturing",
            department="Weaving Operations",
            responsibilities="Overseeing 40 rapier looms, shift output, and loom downtime reconciliation",
        )
        self.visitor.set_access_token(self.token)
        self.visitor.update_completion_status()
        self.visitor.save()

        self.visitor.consents.create(
            category=ConsentCategory.ESSENTIAL,
            status=ConsentStatus.GRANTED,
        )

    @override_settings(AI_PROVIDER="mock")
    def test_orchestration_passes_tailored_profession_directives_to_provider(self):
        from apps.ai_engine.models import Conversation
        from apps.ai_engine.services.orchestration import ConsultationOrchestrationService
        from apps.ai_engine.providers.mock_provider import MockLLMProvider

        conv = Conversation.objects.create(
            visitor=self.visitor,
            title="Loom Line Downtime Investigation",
        )

        mock_provider = MockLLMProvider()
        with patch("apps.ai_engine.services.orchestration.get_ai_provider", return_value=mock_provider):
            assistant_msg = ConsultationOrchestrationService.execute_turn(
                conversation=conv,
                user_content="We are losing 4 hours per day due to rapier loom breakdown and unrecorded stoppages.",
                client_message_id="test-turn-prod-001",
            )

        self.assertIsNotNone(assistant_msg)
        conv.refresh_from_db()
        self.assertEqual(conv.consultation_state.get("profession_category"), "production_manufacturing")

        # Verify Mock provider received profession-tailored system instructions
        self.assertGreater(len(mock_provider.call_history), 0)
        last_req = mock_provider.call_history[-1]
        self.assertIn("Production & Manufacturing Management", last_req.system_instruction)
        self.assertIn("Overall Equipment Effectiveness (OEE)", last_req.system_instruction)
        self.assertIn("Apex Weaving Mills", last_req.system_instruction)
        self.assertIn("Textile Manufacturing", last_req.system_instruction)

    @override_settings(AI_PROVIDER="mock")
    def test_orchestration_adapts_to_software_engineer(self):
        from apps.visitors.models import Visitor, ConsentCategory, ConsentStatus
        from apps.ai_engine.models import Conversation
        from apps.ai_engine.services.orchestration import ConsultationOrchestrationService
        from apps.ai_engine.providers.mock_provider import MockLLMProvider
        import secrets

        sw_token = secrets.token_urlsafe(32)
        sw_visitor = Visitor.objects.create(
            display_name="Devin Thorne",
            email="devin@fintech.example.com",
            profession="Senior Backend Software Engineer",
            company_name="Apex Payments",
            industry="FinTech / Cloud Services",
            department="Core Banking API",
            responsibilities="Scaling high-throughput payment transaction pipelines",
        )
        sw_visitor.set_access_token(sw_token)
        sw_visitor.update_completion_status()
        sw_visitor.save()
        sw_visitor.consents.create(category=ConsentCategory.ESSENTIAL, status=ConsentStatus.GRANTED)

        conv = Conversation.objects.create(
            visitor=sw_visitor,
            title="API Latency & Database Query Bottlenecks",
        )

        mock_provider = MockLLMProvider()
        with patch("apps.ai_engine.services.orchestration.get_ai_provider", return_value=mock_provider):
            assistant_msg = ConsultationOrchestrationService.execute_turn(
                conversation=conv,
                user_content="Our payment gateway latency spikes to 2500ms under 500 RPS concurrency.",
                client_message_id="test-turn-sw-001",
            )

        self.assertIsNotNone(assistant_msg)
        conv.refresh_from_db()
        self.assertEqual(conv.consultation_state.get("profession_category"), "software_it")

        self.assertGreater(len(mock_provider.call_history), 0)
        last_req = mock_provider.call_history[-1]
        self.assertIn("Software Engineering & Enterprise IT", last_req.system_instruction)
        self.assertIn("API latency", last_req.system_instruction)

    @override_settings(AI_PROVIDER="mock")
    def test_profession_correction_dynamically_adapts_subsequent_turns(self):
        from apps.ai_engine.models import Conversation
        from apps.ai_engine.services.orchestration import ConsultationOrchestrationService
        from apps.ai_engine.providers.mock_provider import MockLLMProvider

        conv = Conversation.objects.create(
            visitor=self.visitor,
            title="Dynamic Role Correction Test",
        )

        mock_provider_1 = MockLLMProvider()
        with patch("apps.ai_engine.services.orchestration.get_ai_provider", return_value=mock_provider_1):
            # Turn 1: Starts as Textile Production Manager
            ConsultationOrchestrationService.execute_turn(
                conversation=conv,
                user_content="Investigating line 2 stoppage.",
                client_message_id="corr-turn-001",
            )
        conv.refresh_from_db()
        self.assertEqual(conv.consultation_state.get("profession_category"), "production_manufacturing")

        # Visitor updates their role to Maintenance & Reliability Engineer
        self.visitor.profession = "Plant Maintenance Engineer"
        self.visitor.department = "Mechanical Maintenance"
        self.visitor.responsibilities = "Preventive maintenance and spare parts inventory"
        self.visitor.save()

        mock_provider_2 = MockLLMProvider()
        with patch("apps.ai_engine.services.orchestration.get_ai_provider", return_value=mock_provider_2):
            # Turn 2: Subsequent turn dynamically inherits the new profession
            ConsultationOrchestrationService.execute_turn(
                conversation=conv,
                user_content="Looking into bearing wear and spare motor replacement.",
                client_message_id="corr-turn-002",
            )
        conv.refresh_from_db()
        self.assertEqual(conv.consultation_state.get("profession_category"), "maintenance_reliability")

        self.assertGreater(len(mock_provider_2.call_history), 0)
        last_req = mock_provider_2.call_history[-1]
        self.assertIn("Maintenance & Reliability Engineering", last_req.system_instruction)
        self.assertIn("MTBF", last_req.system_instruction)



