"""
Management command to safely verify OpenAI provider accessibility and model configuration.
Manual execution only: Not called during tests or normal application startup.
Strictly redacts API keys and secrets from output.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import sys

class Command(BaseCommand):
    help = "Verify AI provider configuration and connectivity without revealing secrets."

    def handle(self, *args, **options):
        provider = getattr(settings, "AI_PROVIDER", "openai").strip().lower()
        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini").strip()
        api_key = getattr(settings, "OPENAI_API_KEY", "").strip()

        self.stdout.write(self.style.NOTICE("=== CALDIM IntelliSolve AI — Provider Verification ==="))
        self.stdout.write(f"Configured Provider: {provider}")
        self.stdout.write(f"Target Model: {model}")

        if provider == "mock":
            self.stdout.write(self.style.SUCCESS("[OK] Mock AI Provider is active. Network requests are disabled."))
            return

        if provider != "openai":
            self.stdout.write(self.style.ERROR(f"[ERROR] Unsupported provider: {provider}"))
            sys.exit(1)

        if not api_key:
            self.stdout.write(self.style.ERROR("[ERROR] OPENAI_API_KEY is missing or empty in backend environment."))
            self.stdout.write("Please configure OPENAI_API_KEY in backend/.env before running live queries.")
            sys.exit(1)

        # Indicate key is loaded without exposing any characters
        self.stdout.write("[INFO] OPENAI_API_KEY is populated in backend environment (key hidden for security).")
        self.stdout.write("[INFO] Verifying model availability via read-only model catalogue check...")

        try:
            import openai
            client = openai.OpenAI(api_key=api_key, timeout=15.0)
            # Read-only check for model availability
            model_info = client.models.retrieve(model)
            self.stdout.write(
                self.style.SUCCESS(
                    f"[SUCCESS] OpenAI API connection verified. Model '{model_info.id}' is active and accessible."
                )
            )
        except openai.AuthenticationError:
            self.stdout.write(
                self.style.ERROR(
                    "[ERROR] Authentication failed (HTTP 401). The configured OPENAI_API_KEY was rejected by OpenAI."
                )
            )
            sys.exit(1)
        except openai.RateLimitError:
            self.stdout.write(
                self.style.WARNING(
                    "[WARNING] Rate limit or quota reached (HTTP 429). Check your OpenAI account billing and credits."
                )
            )
            sys.exit(1)
        except openai.NotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f"[ERROR] Model '{model}' not found in accessible OpenAI catalogue. Check your model ID or organization permissions."
                )
            )
            sys.exit(1)
        except Exception as exc:
            # Strictly sanitize exception to ensure zero credential leakage
            err_msg = str(exc).replace(api_key, "[REDACTED_API_KEY]")
            self.stdout.write(self.style.ERROR(f"[ERROR] Provider check failed: {err_msg}"))
            sys.exit(1)
