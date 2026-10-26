import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import (
    Visitor,
    VisitorConsent,
    VisitorSession,
    ProfileCompletionStatus,
    ConsentCategory,
    ConsentStatus,
    SessionStatus,
)

class VisitorModelAndAPITests(TestCase):
    """
    Automated test suite for Phase 2: PostgreSQL Visitor persistence,
    consent management, session establishment, and access control.
    """

    def setUp(self):
        self.client = APIClient()
        self.create_url = reverse("visitor_create")

    def test_create_visitor_with_minimal_data(self):
        """A visitor profile should be creatable with minimal/incomplete data during initial greeting."""
        payload = {
            "display_name": "Dr. Sarah Lin",
            "profession": "Automation Engineer",
        }
        response = self.client.post(self.create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("visitor", data)
        self.assertIn("access_token", data)
        visitor_data = data["visitor"]
        self.assertEqual(visitor_data["display_name"], "Dr. Sarah Lin")
        self.assertEqual(visitor_data["profession"], "Automation Engineer")
        self.assertEqual(visitor_data["profile_completion_status"], ProfileCompletionStatus.PARTIAL)

        # Verify in database
        visitor_obj = Visitor.objects.get(id=visitor_data["id"])
        self.assertEqual(visitor_obj.display_name, "Dr. Sarah Lin")
        self.assertTrue(visitor_obj.verify_access_token(data["access_token"]))

    def test_create_visitor_with_full_profile_and_initial_consent(self):
        """Full visitor profile creation with explicit consent records."""
        payload = {
            "display_name": "Marcus Vance",
            "profession": "Plant Operations Director",
            "company_name": "Apex Precision Mfg",
            "industry": "Automotive Tier 1",
            "department": "Plant Management",
            "responsibilities": "Overseeing 3 assembly lines and evaluating predictive maintenance",
            "email": "marcus.vance@apex-mfg.example.com",
            "phone": "+1-555-019-2834",
            "initial_consents": [
                {
                    "category": ConsentCategory.ESSENTIAL,
                    "status": ConsentStatus.GRANTED,
                    "policy_version": "1.0",
                },
                {
                    "category": ConsentCategory.EMAIL_CONTACT,
                    "status": ConsentStatus.GRANTED,
                    "policy_version": "1.0",
                },
            ],
        }
        response = self.client.post(self.create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        visitor_id = data["visitor"]["id"]
        visitor_obj = Visitor.objects.get(id=visitor_id)
        self.assertEqual(visitor_obj.profile_completion_status, ProfileCompletionStatus.COMPLETE)

        # Verify consents saved in database
        consents = visitor_obj.consents.filter(revoked_at__isnull=True)
        self.assertEqual(consents.count(), 2)
        categories = {c.category for c in consents}
        self.assertIn(ConsentCategory.ESSENTIAL, categories)
        self.assertIn(ConsentCategory.EMAIL_CONTACT, categories)

    def test_invalid_email_and_phone_rejection(self):
        """Invalid email formatting and invalid phone numbers must be rejected."""
        payload = {
            "display_name": "Test User",
            "email": "not-an-email",
            "phone": "12",  # Too short
        }
        response = self.client.post(self.create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())
        self.assertIn("phone", response.json())

    def test_public_visitor_listing_is_strictly_forbidden(self):
        """GET /api/v1/visitors/ must return 405 Method Not Allowed."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unauthorized_profile_access_rejected(self):
        """Attempting to access a visitor profile by UUID without a valid token must return 401."""
        visitor = Visitor.objects.create(display_name="Confidential Executive")
        visitor.set_access_token("valid_token_12345")
        visitor.save()

        detail_url = reverse("visitor_detail", kwargs={"visitor_id": visitor.id})

        # 1. No token header
        resp_no_token = self.client.get(detail_url)
        self.assertEqual(resp_no_token.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Invalid token header
        resp_invalid_token = self.client.get(detail_url, HTTP_X_VISITOR_TOKEN="wrong_guess_token")
        self.assertEqual(resp_invalid_token.status_code, status.HTTP_401_UNAUTHORIZED)

        # 3. Valid token header
        resp_valid_token = self.client.get(detail_url, HTTP_X_VISITOR_TOKEN="valid_token_12345")
        self.assertEqual(resp_valid_token.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_valid_token.json()["visitor"]["display_name"], "Confidential Executive")

    def test_session_establishment_requires_ownership_token(self):
        """Creating a session for a visitor requires proof of token ownership."""
        visitor = Visitor.objects.create(display_name="Kiosk User")
        visitor.set_access_token("session_owner_token_abc")
        visitor.save()

        session_url = reverse("visitor_session_create", kwargs={"visitor_id": visitor.id})

        # Without token -> 401
        resp_unauth = self.client.post(session_url, {"metadata": {"screen": "1080p"}}, format="json")
        self.assertEqual(resp_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # With valid token -> 201 Created
        resp_auth = self.client.post(
            session_url,
            {"metadata": {"screen": "1080p", "browser": "Chrome"}},
            format="json",
            HTTP_X_VISITOR_TOKEN="session_owner_token_abc"
        )
        self.assertEqual(resp_auth.status_code, status.HTTP_201_CREATED)
        session_data = resp_auth.json()
        self.assertEqual(session_data["status"], SessionStatus.ACTIVE)
        self.assertEqual(session_data["metadata"]["screen"], "1080p")

        # Verify DB relation
        session_obj = VisitorSession.objects.get(id=session_data["id"])
        self.assertEqual(session_obj.visitor, visitor)

    def test_consent_grant_and_atomic_revocation(self):
        """Updating consent revokes prior active consent record atomically without duplicate conflicts."""
        visitor = Visitor.objects.create(display_name="Consent Tester")
        visitor.set_access_token("consent_token_xyz")
        visitor.save()

        consent_url = reverse("visitor_consent_record", kwargs={"visitor_id": visitor.id})
        headers = {"HTTP_X_VISITOR_TOKEN": "consent_token_xyz"}

        # 1. Grant Email Contact
        r1 = self.client.post(
            consent_url,
            {"category": ConsentCategory.EMAIL_CONTACT, "status": ConsentStatus.GRANTED},
            format="json",
            **headers
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        first_consent_id = r1.json()["id"]

        # Verify in DB: 1 active consent
        self.assertEqual(visitor.consents.filter(revoked_at__isnull=True).count(), 1)

        # 2. Change/Revoke Email Contact by posting DENIED
        r2 = self.client.post(
            consent_url,
            {"category": ConsentCategory.EMAIL_CONTACT, "status": ConsentStatus.DENIED},
            format="json",
            **headers
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        second_consent_id = r2.json()["id"]

        # Verify old consent was revoked and new one is the only active one
        old_consent = VisitorConsent.objects.get(id=first_consent_id)
        self.assertIsNotNone(old_consent.revoked_at)

        new_consent = VisitorConsent.objects.get(id=second_consent_id)
        self.assertIsNone(new_consent.revoked_at)
        self.assertEqual(new_consent.status, ConsentStatus.DENIED)

        # Ensure active count for that category remains exactly 1
        active_count = visitor.consents.filter(
            category=ConsentCategory.EMAIL_CONTACT,
            revoked_at__isnull=True
        ).count()
        self.assertEqual(active_count, 1)

    def test_forbidden_keys_filtered_from_session_metadata(self):
        """Sensitive operational keys (passwords, tokens, etc.) must be filtered from metadata."""
        visitor = Visitor.objects.create(display_name="Security Tester")
        visitor.set_access_token("sec_tok_99")
        visitor.save()

        session_url = reverse("visitor_session_create", kwargs={"visitor_id": visitor.id})
        payload = {
            "metadata": {
                "safe_kiosk_id": "KIOSK-04",
                "password": "secret_password",
                "auth_token": "secret_token",
            }
        }
        res = self.client.post(
            session_url,
            payload,
            format="json",
            HTTP_X_VISITOR_TOKEN="sec_tok_99"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        metadata = res.data["metadata"]
        self.assertIn("safe_kiosk_id", metadata)
        self.assertNotIn("password", metadata)
        self.assertNotIn("auth_token", metadata)

    def test_constant_time_token_verification_cases(self):
        """Constant-time token verification handles valid, invalid, and missing tokens properly."""
        visitor = Visitor.objects.create(display_name="Token Test Subject")
        visitor.set_access_token("valid_token_xyz_123456789012345678")
        visitor.save()

        # 1. Valid token
        self.assertTrue(visitor.verify_access_token("valid_token_xyz_123456789012345678"))

        # 2. Missing token
        self.assertFalse(visitor.verify_access_token(""))
        self.assertFalse(visitor.verify_access_token(None))

        # 3. Completely invalid token
        self.assertFalse(visitor.verify_access_token("wrong_token_entirely"))

        # 4. Off-by-one character (same length)
        self.assertFalse(visitor.verify_access_token("valid_token_xyz_123456789012345679"))

    def test_token_revocation_endpoint_and_access_block(self):
        """Revoking a token stamps revocation time and blocks subsequent authenticated calls."""
        visitor = Visitor.objects.create(display_name="Kiosk Visitor")
        visitor.set_access_token("kiosk_session_token_111")
        visitor.save()

        revoke_url = reverse("visitor_token_revoke", kwargs={"visitor_id": visitor.id})
        detail_url = reverse("visitor_detail", kwargs={"visitor_id": visitor.id})

        # Revoke with valid token -> 200 OK
        resp = self.client.post(revoke_url, HTTP_X_VISITOR_TOKEN="kiosk_session_token_111")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Confirm token_revoked_at is set in DB
        visitor.refresh_from_db()
        self.assertIsNotNone(visitor.token_revoked_at)

        # Subsequent detail request with same token must be rejected with 401
        detail_resp = self.client.get(detail_url, HTTP_X_VISITOR_TOKEN="kiosk_session_token_111")
        self.assertEqual(detail_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_rejected(self):
        """Tokens older than VISITOR_TOKEN_TTL_DAYS must be rejected."""
        import datetime
        from django.utils import timezone

        visitor = Visitor.objects.create(display_name="Expired User")
        visitor.set_access_token("old_token_from_past")
        # Artificially set generation timestamp to 31 days ago (default TTL is 30)
        visitor.token_created_at = timezone.now() - datetime.timedelta(days=31)
        visitor.save()

        self.assertFalse(visitor.verify_access_token("old_token_from_past"))

        detail_url = reverse("visitor_detail", kwargs={"visitor_id": visitor.id})
        resp = self.client.get(detail_url, HTTP_X_VISITOR_TOKEN="old_token_from_past")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_visitor_create_rate_limiting_configured(self):
        """Verify that VisitorCreateView has rate throttling configured."""
        from apps.visitors.views import VisitorCreateView
        self.assertEqual(VisitorCreateView.throttle_scope, "visitor_create")
        self.assertTrue(len(VisitorCreateView.throttle_classes) > 0)

    def test_patch_visitor_progressive_onboarding(self):
        """Visitor can progressively update their profile fields via PATCH with valid token."""
        # 1. Start with initial empty visitor
        resp_init = self.client.post(self.create_url, {}, format="json")
        self.assertEqual(resp_init.status_code, status.HTTP_201_CREATED)
        v_id = resp_init.json()["visitor"]["id"]
        token = resp_init.json()["access_token"]
        patch_url = reverse("visitor_detail", kwargs={"visitor_id": v_id})

        # Step 1: Update full name
        r1 = self.client.patch(patch_url, {"display_name": "Vikram Patel"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.json()["visitor"]["display_name"], "Vikram Patel")
        self.assertEqual(r1.json()["visitor"]["profile_completion_status"], ProfileCompletionStatus.PARTIAL)

        # Step 2: Update email
        r2 = self.client.patch(patch_url, {"email": "vikram.p@patel-eng.example.com"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.json()["visitor"]["email"], "vikram.p@patel-eng.example.com")

        # Step 3: Update phone with country code
        r3 = self.client.patch(patch_url, {"phone": "+91 98765 43210"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r3.status_code, status.HTTP_200_OK)
        self.assertEqual(r3.json()["visitor"]["phone"], "+91 98765 43210")

        # Step 4: Update profession
        r4 = self.client.patch(patch_url, {"profession": "Chief Automation Architect"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r4.status_code, status.HTTP_200_OK)

        # Step 5: Update company
        r5 = self.client.patch(patch_url, {"company_name": "Patel Automation Ltd"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r5.status_code, status.HTTP_200_OK)

        # Step 6: Update industry
        r6 = self.client.patch(patch_url, {"industry": "Heavy Machinery & Robotics"}, format="json", HTTP_X_VISITOR_TOKEN=token)
        self.assertEqual(r6.status_code, status.HTTP_200_OK)

        # Step 7: Update department & responsibilities -> complete
        r7 = self.client.patch(
            patch_url,
            {
                "department": "Plant Engineering",
                "responsibilities": "Supervising automated assembly and SCADA systems",
            },
            format="json",
            HTTP_X_VISITOR_TOKEN=token,
        )
        self.assertEqual(r7.status_code, status.HTTP_200_OK)
        self.assertEqual(r7.json()["visitor"]["profile_completion_status"], ProfileCompletionStatus.COMPLETE)

    def test_patch_rejects_unauthorized_token(self):
        """PATCH /api/v1/visitors/{visitor_id}/ rejects requests without a valid ownership token."""
        visitor = Visitor.objects.create(display_name="Secure User")
        visitor.set_access_token("valid_token_xyz")
        visitor.save()
        patch_url = reverse("visitor_detail", kwargs={"visitor_id": visitor.id})

        # No token -> 401
        res1 = self.client.patch(patch_url, {"display_name": "Hacker Name"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_401_UNAUTHORIZED)

        # Invalid token -> 401
        res2 = self.client.patch(patch_url, {"display_name": "Hacker Name"}, format="json", HTTP_X_VISITOR_TOKEN="bad_token")
        self.assertEqual(res2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_visitor_patch_and_get_isolation(self):
        """Visitor A cannot read or modify Visitor B's profile."""
        visitor_a = Visitor.objects.create(display_name="Visitor A")
        visitor_a.set_access_token("token_a")
        visitor_a.save()

        visitor_b = Visitor.objects.create(display_name="Visitor B")
        visitor_b.set_access_token("token_b")
        visitor_b.save()

        url_b = reverse("visitor_detail", kwargs={"visitor_id": visitor_b.id})

        # Visitor A uses token_a to GET Visitor B -> 401
        res_get = self.client.get(url_b, HTTP_X_VISITOR_TOKEN="token_a")
        self.assertEqual(res_get.status_code, status.HTTP_401_UNAUTHORIZED)

        # Visitor A uses token_a to PATCH Visitor B -> 401
        res_patch = self.client.patch(url_b, {"display_name": "Tampered"}, format="json", HTTP_X_VISITOR_TOKEN="token_a")
        self.assertEqual(res_patch.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_validation_invalid_phone_and_email(self):
        """PATCH validates email and phone formatting."""
        visitor = Visitor.objects.create(display_name="Val Test")
        visitor.set_access_token("tok_val")
        visitor.save()
        patch_url = reverse("visitor_detail", kwargs={"visitor_id": visitor.id})

        # Invalid email
        res_email = self.client.patch(patch_url, {"email": "invalid-email"}, format="json", HTTP_X_VISITOR_TOKEN="tok_val")
        self.assertEqual(res_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res_email.json())

        # Invalid phone (letters or too short)
        res_phone = self.client.patch(patch_url, {"phone": "abc"}, format="json", HTTP_X_VISITOR_TOKEN="tok_val")
        self.assertEqual(res_phone.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", res_phone.json())

    def test_new_consent_categories_recording(self):
        """Visitor can grant and revoke proposal_delivery and marketing consents."""
        visitor = Visitor.objects.create(display_name="Consent User")
        visitor.set_access_token("tok_consent")
        visitor.save()
        consent_url = reverse("visitor_consent_record", kwargs={"visitor_id": visitor.id})
        headers = {"HTTP_X_VISITOR_TOKEN": "tok_consent"}

        # Grant proposal_delivery
        r1 = self.client.post(
            consent_url,
            {"category": ConsentCategory.PROPOSAL_DELIVERY, "status": ConsentStatus.GRANTED},
            format="json",
            **headers,
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r1.json()["category"], "proposal_delivery")

        # Grant marketing
        r2 = self.client.post(
            consent_url,
            {"category": ConsentCategory.MARKETING, "status": ConsentStatus.GRANTED},
            format="json",
            **headers,
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.json()["category"], "marketing")

    def test_progressive_six_question_onboarding_without_phone(self):
        """
        Progressive 6-question onboarding (Name -> Email -> Profession -> Company -> Industry -> Dept/Resp)
        completes visitor profile without requiring phone number.
        """
        # Step 0: Minimal creation with initial greeting
        res0 = self.client.post(self.create_url, {"display_name": "Marcus Vance"}, format="json")
        self.assertEqual(res0.status_code, status.HTTP_201_CREATED)
        visitor_id = res0.json()["visitor"]["id"]
        token = res0.json()["access_token"]
        patch_url = reverse("visitor_detail", kwargs={"visitor_id": visitor_id})
        headers = {"HTTP_X_VISITOR_TOKEN": token}

        # Step 1: Provide Email
        res1 = self.client.patch(patch_url, {"email": "marcus.vance@mfg.com"}, format="json", **headers)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.json()["visitor"]["profile_completion_status"], "partial")

        # Step 2: Provide Profession
        res2 = self.client.patch(patch_url, {"profession": "Production Manager"}, format="json", **headers)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.json()["visitor"]["profile_completion_status"], "partial")

        # Step 3: Provide Company
        res3 = self.client.patch(patch_url, {"company_name": "Vance Industrial"}, format="json", **headers)
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.json()["visitor"]["profile_completion_status"], "partial")

        # Step 4: Provide Industry
        res4 = self.client.patch(patch_url, {"industry": "Precision Machining"}, format="json", **headers)
        self.assertEqual(res4.status_code, status.HTTP_200_OK)
        self.assertEqual(res4.json()["visitor"]["profile_completion_status"], "partial")

        # Step 5: Provide Department & Responsibilities -> Completes profile
        res5 = self.client.patch(
            patch_url,
            {"department": "Shopfloor Operations", "responsibilities": "Managing 15 CNC cells and OEE tracking"},
            format="json",
            **headers,
        )
        self.assertEqual(res5.status_code, status.HTTP_200_OK)
        self.assertEqual(res5.json()["visitor"]["profile_completion_status"], "complete")

        # Verify in database: phone remains empty and completion is COMPLETE
        v_db = Visitor.objects.get(id=visitor_id)
        self.assertFalse(v_db.phone)
        self.assertEqual(v_db.profile_completion_status, ProfileCompletionStatus.COMPLETE)


