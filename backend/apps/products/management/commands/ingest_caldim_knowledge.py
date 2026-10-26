"""
CALDIM Knowledge Ingestion Management Command.
Seeds CALDIM product models, capabilities, documented limitations,
industry problem mappings, and reference documents as DRAFT / UNVERIFIED records.
Includes safety shield preventing overwrite of human-verified records.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

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


class Command(BaseCommand):
    help = "Seeds CALDIM product reference catalogue as draft/unverified records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-chunking even if content hash has not changed.",
        )
        parser.add_argument(
            "--overwrite-verified",
            action="store_true",
            help="Allow overwriting previously verified product records with draft sample content.",
        )

    def handle(self, *args, **options):
        force_reingest = options.get("force", False)
        overwrite_verified = options.get("overwrite_verified", False)
        self.stdout.write(self.style.MIGRATE_HEADING("Starting CALDIM Product Knowledge Ingestion (DRAFT MODE)..."))

        with transaction.atomic():
            self._seed_caltims(force_reingest, overwrite_verified)
            self._seed_calrims(force_reingest, overwrite_verified)
            self._seed_calbuy(force_reingest, overwrite_verified)
            self._seed_caltrack(force_reingest, overwrite_verified)
            self._seed_calems(force_reingest, overwrite_verified)
            self._seed_calmisc(force_reingest, overwrite_verified)
            self._seed_wms(force_reingest, overwrite_verified)
            self._seed_asset_management(force_reingest, overwrite_verified)
            self._seed_project_management(force_reingest, overwrite_verified)

        total_products = Product.objects.count()
        total_caps = ProductCapability.objects.count()
        total_limits = ProductLimitation.objects.count()
        total_mappings = IndustryProblemMapping.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCALDIM Knowledge Ingestion Complete (Draft / Gated Mode)!\n"
                f"- Total Products: {total_products}\n"
                f"- Total Capabilities: {total_caps}\n"
                f"- Total Limitations: {total_limits}\n"
                f"- Total Industry Mappings: {total_mappings}\n"
            )
        )

    def _check_safety_shield(self, slug: str, overwrite_verified: bool) -> bool:
        """Return True if safe to proceed; False if shielded verified record."""
        existing = Product.objects.filter(slug=slug).first()
        if existing and existing.is_verified and not overwrite_verified:
            self.stdout.write(
                self.style.WARNING(
                    f"  [SAFETY SHIELD] Product '{slug}' is human-verified in database. "
                    f"Skipping overwrite with draft content. Use --overwrite-verified to force."
                )
            )
            return False
        return True

    def _seed_caltims(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("caltims", overwrite_verified):
            return

        product, _ = Product.objects.update_or_create(
            slug="caltims",
            defaults={
                "name": "CALTIMS",
                "category": "HR & Payroll Engine",
                "tagline": "Sync timesheets to payroll instantly.",
                "overview": (
                    "Core timesheet and payroll automation engine from CALDIM Software Division (CALDIM-DAS). "
                    "Bridges the gap between daily work logs and month-end payroll by calculating leaves, task allocations, "
                    "and tax deductions automatically without manual intervention. Listed under Planned Capabilities with Request Preview Access."
                ),
                "readiness_status": ProductReadinessStatus.PREVIEW_READY,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verifier_name": "",
                "last_verified_at": None,
                "customization_scope": (
                    "CALDIM custom software division can prioritize the integration and rollout of this module based on client business requirements."
                ),
                "verified_source_url": "https://caldimproducts.com/products/caltims",
                "demo_url": "",
                "video_preview_title": "",
                "video_preview_description": "",
                "hero_image_url": "",
                "pricing_status": "Unverified / Contact Sales",
                "pricing_evidence": "",
                "notes": "DRAFT RECORD: Verified against live website text. Fabricated metrics removed. Gated pending human product owner sign-off.",
            },
        )

        capabilities = [
            (
                "Log Weekly Timesheets [PLANNED/PREVIEW]",
                "Submits work hours against assigned projects using a clean spreadsheet grid.",
                "Eliminates hours of manual entry",
                1,
            ),
            (
                "Manage Employee Leaves [PLANNED/PREVIEW]",
                "Syncs approved time-off requests directly to active timesheet grids automatically.",
                "Automatic timesheet grid synchronization",
                2,
            ),
            (
                "Run Monthly Payroll [PLANNED/PREVIEW]",
                "Auto-calculates earnings, deductions, and tax slabs from approved time logs.",
                "Zero Legal Mistakes: Automates Indian tax slabs, PF, and ESI rules",
                3,
            ),
            (
                "Export Bank Transfers [PLANNED/PREVIEW]",
                "Downloads direct banking-portal-ready payment files in one click.",
                "One-click banking portal payment file generation",
                4,
            ),
            (
                "Configure Users & Roles [PLANNED/PREVIEW]",
                "Secures sensitive workforce financial data through granular permission tables.",
                "Module-level permissions and audit logs",
                5,
            ),
            (
                "Generate Custom Reports [PLANNED/PREVIEW]",
                "Analyzes team utilization and historical payroll costs in seconds.",
                "Live employee utilization rates and historical cost reports",
                6,
            ),
        ]

        for title, desc, metric, order in capabilities:
            ProductCapability.objects.update_or_create(
                product=product,
                title=title,
                defaults={
                    "description": desc,
                    "metric_highlight": metric,
                    "feature_order": order,
                    "is_verified": False,
                },
            )

        limitations = [
            (
                "Custom Module Rollout Prerequisite",
                "CALTIMS is listed as a custom module rollout prioritized by CALDIM engineers based on enterprise client requirements.",
                "Clients engage via direct preview access request on official portal.",
            ),
        ]

        for title, desc, mitigation in limitations:
            ProductLimitation.objects.update_or_create(
                product=product,
                title=title,
                defaults={"description": desc, "mitigation_or_alternative": mitigation},
            )

        problems = [
            (
                "Multi-Facility Enterprises",
                "Manual Timesheet Calculation and Payroll Overhead",
                "Syncs timesheets directly to payroll to eliminate manual entry and automate Indian tax slabs, PF, and ESI compliance rules.",
                "HR Operations / Finance Controller",
            ),
        ]

        for ind, prob, sol, prof in problems:
            IndustryProblemMapping.objects.update_or_create(
                product=product,
                industry=ind,
                business_problem=prob,
                defaults={"solution_summary": sol, "target_profession": prof},
            )

        # Ingest reference document as DRAFT (is_approved=False)
        caltims_doc_text = """
CALTIMS HR & PAYROLL ENGINE
Official Reference & Specification [DRAFT]

System Overview:
Our core timesheet and payroll automation engine. CALTIMS bridges the gap between daily work logs and month-end payroll by calculating leaves, task allocations, and tax deductions automatically without manual intervention.

Key System Features:
1. Log Weekly Timesheets: Submits work hours against assigned projects using a clean spreadsheet grid.
2. Manage Employee Leaves: Syncs approved time-off requests directly to active timesheet grids automatically.
3. Run Monthly Payroll: Auto-calculates earnings, deductions, and tax slabs from approved time logs.
4. Export Bank Transfers: Downloads direct banking-portal-ready payment files in one click.
5. Configure Users & Roles: Secures sensitive workforce financial data through granular permission tables.
6. Generate Custom Reports: Analyzes team utilization and historical payroll costs in seconds.

Business Impact:
- Save Administrative Days: Syncs timesheets directly to payroll to eliminate hours of manual entry.
- Zero Legal Mistakes: Automates Indian tax slabs, PF, and ESI rules to guarantee compliance.
- Total Project Visibility: Displays live employee utilization rates and time allocation on one dashboard.
- Secure Payroll Privacy: Restricts sensitive financial access through module-level permissions and audit logs.

Corporate Information:
- Head Office: Minimac Center #118, First Floor, Arcot Road, Valasaravakkam, Chennai, Tamil Nadu – 600087
- Branch Office: Plot No. 22, 23, 24, 2nd Floor, Durga Bhavani Towers, Bagalur Road, Hosur, Tamil Nadu – 635103
- D-U-N-S: 86-039-9952
        """.strip()

        res = KnowledgeIngestionService.ingest_document(
            product=product,
            title="CALTIMS Reference Specification [DRAFT]",
            source_url="https://caldimproducts.com/products/caltims",
            raw_text=caltims_doc_text,
            document_type=ProductDocumentType.OFFICIAL_WEBPAGE,
            version="1.0-draft",
            approved_by="Pending Product Owner Review",
            is_approved=False,  # Strictly unapproved until human sign-off
            section_title="CALTIMS Overview",
            force_reingest=force,
        )
        self.stdout.write(f"  Ingested CALTIMS document chunks: {res['chunk_count']} (draft/unapproved)")

    def _seed_calrims(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("calrims", overwrite_verified):
            return
        product, _ = Product.objects.update_or_create(
            slug="calrims",
            defaults={
                "name": "CALRIMS",
                "category": "Recruitment Intelligence & Applicant Tracking",
                "tagline": "Automated candidate sourcing, resume intelligence, and interview pipeline",
                "overview": "Recruitment and applicant management platform designed to automate resume intake, candidate matching against job roles, and multi-round interview tracking.",
                "readiness_status": ProductReadinessStatus.PREVIEW_READY,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: Sourced from CALDIM-DAS showcase.",
            },
        )
        ProductCapability.objects.update_or_create(
            product=product,
            title="Resume Intelligence & Semantic Parser [ILLUSTRATIVE]",
            defaults={
                "description": "Extracts skills, project experience, and employment tenure from PDF/Word resumes.",
                "metric_highlight": "Preview feature observed in showcase",
                "feature_order": 1,
                "is_verified": False,
            },
        )

    def _seed_calbuy(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("calbuy", overwrite_verified):
            return
        product, _ = Product.objects.update_or_create(
            slug="calbuy",
            defaults={
                "name": "CALBUY",
                "category": "Procurement & Vendor Lifecycle Pipeline",
                "tagline": "Streamlined purchase requisitions, RFQs, vendor comparisons, and PO issuance",
                "overview": "Corporate purchasing workflow system supporting requisitions, quotation requests, supplier comparison, and purchase order tracking.",
                "readiness_status": ProductReadinessStatus.PREVIEW_READY,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: Sourced from CALDIM-DAS showcase.",
            },
        )
        ProductCapability.objects.update_or_create(
            product=product,
            title="Requisition to Purchase Order Workflow [ILLUSTRATIVE]",
            defaults={
                "description": "Multi-tier approval routing based on order value, budget center, and authority limits.",
                "metric_highlight": "Preview feature observed in showcase",
                "feature_order": 1,
                "is_verified": False,
            },
        )

    def _seed_caltrack(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("caltrack", overwrite_verified):
            return
        product, _ = Product.objects.update_or_create(
            slug="caltrack",
            defaults={
                "name": "CALTRACK",
                "category": "Field Operations & Logistics Tracking",
                "tagline": "Real-time field engineer dispatch, job ticketing, and proof-of-service capture",
                "overview": "Field service dispatch solution for coordinating mobile service technicians, logging GPS-verified job completion, and capturing customer digital signatures.",
                "readiness_status": ProductReadinessStatus.PREVIEW_READY,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: Sourced from CALDIM-DAS showcase.",
            },
        )

    def _seed_calems(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("calems", overwrite_verified):
            return
        Product.objects.update_or_create(
            slug="calems",
            defaults={
                "name": "CALEMS",
                "category": "Enterprise Equipment & Maintenance Management",
                "tagline": "Preventive maintenance scheduling and machine downtime analytics",
                "overview": "Computerized maintenance management system (CMMS) in active development to schedule preventive machine servicing.",
                "readiness_status": ProductReadinessStatus.IN_DEVELOPMENT,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: In active development.",
            },
        )

    def _seed_calmisc(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("calmisc", overwrite_verified):
            return
        Product.objects.update_or_create(
            slug="calmisc",
            defaults={
                "name": "CALMISC",
                "category": "Structural Steel & Material Takeoff Estimation",
                "tagline": "Specialized material cost calculation and structural fabrication estimating",
                "overview": "Domain-specific engineering estimation engine for steel fabricators and pre-engineered building contractors.",
                "readiness_status": ProductReadinessStatus.IN_DEVELOPMENT,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: In active development.",
            },
        )

    def _seed_wms(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("caldim-wms", overwrite_verified):
            return
        Product.objects.update_or_create(
            slug="caldim-wms",
            defaults={
                "name": "Warehouse Management",
                "category": "Intralogistics & Inventory Operations",
                "tagline": "Bin-level inventory allocation, batch control, and barcode pick-pack workflows",
                "overview": "Intralogistics platform supporting multi-warehouse stock allocation, FIFO/LIFO tracking, and handheld barcode scanning.",
                "readiness_status": ProductReadinessStatus.IN_DEVELOPMENT,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: In active development.",
            },
        )

    def _seed_asset_management(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("caldim-asset-management", overwrite_verified):
            return
        Product.objects.update_or_create(
            slug="caldim-asset-management",
            defaults={
                "name": "Asset Management",
                "category": "Fixed Asset Lifecycle & Depreciation",
                "tagline": "Enterprise physical asset tracking, barcode tagging, and financial depreciation",
                "overview": "Fixed asset registry tracking hardware, tooling, and plant machinery through acquisition and depreciation.",
                "readiness_status": ProductReadinessStatus.IN_DEVELOPMENT,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: In active development.",
            },
        )

    def _seed_project_management(self, force: bool, overwrite_verified: bool):
        if not self._check_safety_shield("caldim-project-management", overwrite_verified):
            return
        Product.objects.update_or_create(
            slug="caldim-project-management",
            defaults={
                "name": "Project Management",
                "category": "Industrial Project Tracking & Milestones",
                "tagline": "Milestone scheduling, critical path tracking, and engineering resource allocation",
                "overview": "Roadmap conceptual platform intended to link engineering timesheets with Gantt milestones.",
                "readiness_status": ProductReadinessStatus.CONCEPT,
                "publication_status": ProductPublicationStatus.DRAFT,
                "is_active": True,
                "is_verified": False,
                "verified_source_url": "https://caldimproducts.com/products",
                "notes": "DRAFT RECORD: Concept stage only.",
            },
        )
