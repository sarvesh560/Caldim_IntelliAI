"""
CALDIM Catalogue Validation and Import Management Command.
Provides schema validation, dry-run previews, and idempotent importing
from backend/knowledge_base/caldim_products/products.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.products.models import (
    Product,
    ProductReadinessStatus,
    ProductPublicationStatus,
    ProductCapability,
    ProductLimitation,
    IndustryProblemMapping,
    ProductMedia,
    ProductMediaType,
    ProductDocumentType,
)
from apps.products.services.ingestion import KnowledgeIngestionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Validates and idempotently imports products from products.json catalogue with dry-run support."

    def add_arguments(self, parser):
        default_catalogue = settings.BASE_DIR / "knowledge_base" / "caldim_products" / "products.json"
        parser.add_argument(
            "--file",
            type=str,
            default=str(default_catalogue),
            help=f"Path to catalogue JSON file (defaults to {default_catalogue})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate schema and preview changes without writing to the database.",
        )
        parser.add_argument(
            "--overwrite-verified",
            action="store_true",
            help="Allow overwriting previously verified products with unverified sample records.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{'[DRY-RUN] ' if dry_run else ''}Loading CALDIM Catalogue from: {file_path}"
            )
        )

        if not file_path.exists():
            raise CommandError(f"Catalogue file not found at: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in {file_path}: {e}")

        products_data = data.get("products", [])
        if not products_data:
            raise CommandError("No 'products' array found in catalogue file.")

        # Run strict validation
        errors, warnings, valid_products = self._validate_catalogue(products_data, file_path.parent)

        if errors:
            self.stdout.write(self.style.ERROR(f"\nValidation failed with {len(errors)} error(s):"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f"  - {err}"))
            raise CommandError("Catalogue validation failed. Please fix the errors listed above.")

        if warnings:
            self.stdout.write(self.style.WARNING(f"\nValidation Warnings ({len(warnings)}):"))
            for warn in warnings:
                self.stdout.write(self.style.WARNING(f"  ! {warn}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nSchema validation passed for all {len(valid_products)} products.")
        )

        if dry_run:
            self._display_dry_run_summary(valid_products)
            return

        # Execute idempotent database write inside an atomic transaction
        self._execute_import(valid_products, file_path.parent, overwrite_verified=options.get("overwrite_verified", False))

    def _validate_catalogue(self, products: List[Dict[str, Any]], base_dir: Path):
        errors = []
        warnings = []
        valid_products = []
        seen_slugs = set()

        valid_readiness = set(ProductReadinessStatus.values)
        valid_publications = set(ProductPublicationStatus.values)

        for idx, item in enumerate(products, start=1):
            name = item.get("name", "").strip()
            slug = item.get("slug", "").strip()
            category = item.get("category", "").strip()
            readiness = item.get("readiness_status", "").strip()
            publication = item.get("publication_status", "draft").strip()
            is_verified = item.get("is_verified", False)

            if not name:
                errors.append(f"Product #{idx}: 'name' is required.")
            if not slug:
                errors.append(f"Product #{idx} ({name or 'Unnamed'}): 'slug' is required.")
            elif slug in seen_slugs:
                errors.append(f"Duplicate slug '{slug}' found on product #{idx} ({name}).")
            else:
                seen_slugs.add(slug)

            if not category:
                errors.append(f"Product '{slug}': 'category' is required.")

            if readiness not in valid_readiness:
                errors.append(
                    f"Product '{slug}': Invalid readiness_status '{readiness}'. "
                    f"Allowed: {sorted(list(valid_readiness))}"
                )

            if publication not in valid_publications:
                errors.append(
                    f"Product '{slug}': Invalid publication_status '{publication}'. "
                    f"Allowed: {sorted(list(valid_publications))}"
                )

            # Verification governance checks
            if is_verified:
                if not item.get("verifier_name"):
                    warnings.append(f"Product '{slug}': is_verified=true but 'verifier_name' is missing.")
                if not item.get("verification_date"):
                    warnings.append(f"Product '{slug}': is_verified=true but 'verification_date' is missing.")
                if not item.get("official_product_page"):
                    warnings.append(f"Product '{slug}': is_verified=true but 'official_product_page' is missing.")
            else:
                if publication == "published":
                    warnings.append(
                        f"Product '{slug}': publication_status='published' but is_verified=false. "
                        f"Unverified records are gated from authoritative AI consultation."
                    )

            valid_products.append(item)

        return errors, warnings, valid_products

    def _display_dry_run_summary(self, products: List[Dict[str, Any]]):
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- DRY RUN PREVIEW SUMMARY ---"))
        verified_count = sum(1 for p in products if p.get("is_verified"))
        unverified_count = len(products) - verified_count

        self.stdout.write(f"Total Products to Import/Update: {len(products)}")
        self.stdout.write(f"  - Verified Products (Admitted to AI Consultation): {verified_count}")
        self.stdout.write(f"  - Sample / Illustrative Products (Strictly Gated): {unverified_count}")

        status_counts = {}
        for p in products:
            st = p.get("readiness_status", "unknown")
            status_counts[st] = status_counts.get(st, 0) + 1

        self.stdout.write("\nReadiness Breakdown:")
        for st, count in status_counts.items():
            self.stdout.write(f"  - {st}: {count}")

        self.stdout.write("\nProduct Inventory:")
        for p in products:
            v_tag = "VERIFIED" if p.get("is_verified") else "UNVERIFIED/SAMPLE"
            caps = len(p.get("capabilities", []))
            limits = len(p.get("limitations", []))
            probs = len(p.get("business_problems", []))
            self.stdout.write(
                f"  [{v_tag:18}] {p['name']:<25} ({p['slug']}) — {p['readiness_status']} "
                f"| Caps: {caps}, Limits: {limits}, Probs: {probs}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n[DRY-RUN COMPLETED] No changes were written to the database. "
                "Run without --dry-run to commit changes."
            )
        )

    @transaction.atomic
    def _execute_import(self, products: List[Dict[str, Any]], base_dir: Path, overwrite_verified: bool = False):
        self.stdout.write(self.style.MIGRATE_HEADING("\nExecuting idempotent database import..."))

        created_count = 0
        updated_count = 0
        skipped_verified_count = 0
        total_caps = 0
        total_limits = 0
        total_probs = 0
        total_media = 0

        for item in products:
            slug = item["slug"]

            # Safety shield: never overwrite an existing verified product with unverified sample data
            existing_prod = Product.objects.filter(slug=slug).first()
            if existing_prod and existing_prod.is_verified and not item.get("is_verified", False):
                if not overwrite_verified:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [SAFETY SHIELD] Product '{slug}' is verified in database. "
                            f"Skipping overwrite with unverified sample data. Use --overwrite-verified to force."
                        )
                    )
                    skipped_verified_count += 1
                    continue
            product_defaults = {
                "name": item["name"],
                "category": item["category"],
                "tagline": item.get("tagline", ""),
                "overview": item.get("overview", ""),
                "readiness_status": item.get("readiness_status", ProductReadinessStatus.IN_DEVELOPMENT),
                "publication_status": item.get("publication_status", ProductPublicationStatus.DRAFT),
                "is_active": item.get("is_active", True),
                "is_verified": item.get("is_verified", False),
                "verifier_name": item.get("verifier_name") or "",
                "last_verified_at": timezone.now() if item.get("is_verified") else None,
                "customization_scope": item.get("customization_scope", ""),
                "integrations": item.get("integrations", []),
                "deployment_options": item.get("deployment_options", []),
                "verified_source_url": item.get("official_product_page") or "",
                "documentation_url": item.get("documentation_url") or "",
                "demo_url": item.get("demo_url") or "",
                "video_preview_title": item.get("video_preview_title", ""),
                "video_preview_description": item.get("video_preview_description", ""),
                "hero_image_url": item.get("hero_image_url", ""),
                "pricing_status": item.get("pricing_status", "Custom Enterprise Quote"),
                "pricing_evidence": item.get("pricing_evidence") or "",
                "case_studies": item.get("case_studies", []),
                "customer_references": item.get("customer_references", []),
                "source_references": item.get("source_references", []),
                "notes": item.get("notes", ""),
            }

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults=product_defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            # Import Capabilities
            for cap in item.get("capabilities", []):
                title = cap.get("title", "").strip()
                if not title:
                    continue
                ProductCapability.objects.update_or_create(
                    product=product,
                    title=title,
                    defaults={
                        "description": cap.get("description", ""),
                        "metric_highlight": cap.get("metric_highlight", ""),
                        "feature_order": cap.get("feature_order", 0),
                        "is_verified": cap.get("is_verified", False),
                    },
                )
                total_caps += 1

            # Import Limitations
            for lim in item.get("limitations", []):
                title = lim.get("title", "").strip()
                if not title:
                    continue
                ProductLimitation.objects.update_or_create(
                    product=product,
                    title=title,
                    defaults={
                        "description": lim.get("description", ""),
                        "mitigation_or_alternative": lim.get("mitigation_or_alternative", ""),
                    },
                )
                total_limits += 1

            # Import Business Problems
            for prob in item.get("business_problems", []):
                industry = prob.get("industry", "").strip()
                problem_name = prob.get("business_problem", "").strip()
                if not industry or not problem_name:
                    continue
                IndustryProblemMapping.objects.update_or_create(
                    product=product,
                    industry=industry,
                    business_problem=problem_name,
                    defaults={
                        "solution_summary": prob.get("solution_summary", ""),
                        "target_profession": prob.get("target_profession", ""),
                    },
                )
                total_probs += 1

            # Import Media
            for m in item.get("media", []):
                title = m.get("title", "").strip()
                url = m.get("url", "").strip()
                if not title or not url:
                    continue
                ProductMedia.objects.update_or_create(
                    product=product,
                    title=title,
                    defaults={
                        "media_type": m.get("media_type", ProductMediaType.SCREENSHOT),
                        "url": url,
                        "caption": m.get("caption", ""),
                        "display_order": m.get("display_order", 0),
                        "is_approved": m.get("is_approved", False),
                    },
                )
                total_media += 1

            # Check for corresponding markdown document in documents/
            doc_file = base_dir / "documents" / f"{slug}_spec.md"
            if doc_file.exists():
                try:
                    with open(doc_file, "r", encoding="utf-8") as df:
                        raw_doc_text = df.read()
                    KnowledgeIngestionService.ingest_document(
                        product=product,
                        title=f"{product.name} Official Specification Document",
                        source_url=product.verified_source_url or f"https://caldimproducts.com/products/{slug}",
                        raw_text=raw_doc_text,
                        document_type=ProductDocumentType.SPECIFICATION_SHEET,
                        version="1.0",
                        approved_by="CALDIM Product Operations",
                        is_approved=product.is_verified,
                        section_title=f"{product.name} Specifications",
                    )
                except Exception as e:
                    logger.warning("Could not ingest document %s: %s", doc_file, e)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCatalogue import completed successfully!\n"
                f"- Products Created: {created_count}\n"
                f"- Products Updated: {updated_count}\n"
                f"- Total Capabilities: {total_caps}\n"
                f"- Total Limitations: {total_limits}\n"
                f"- Total Business Problem Mappings: {total_probs}\n"
                f"- Total Media Assets: {total_media}\n"
            )
        )
