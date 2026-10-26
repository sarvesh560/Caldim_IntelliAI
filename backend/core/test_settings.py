"""
Dedicated isolated test settings for CALDIM IntelliSolve.
Inherits all configurations, installed apps, DRF throttles, and models from core.settings.
Provides an isolated, ephemeral in-memory database to allow automated test execution
without risking live PostgreSQL data or requiring CREATEDB role escalation.
"""
from core.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Automated tests strictly use the isolated mock provider; zero network or API credits
AI_PROVIDER = "mock"

