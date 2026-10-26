"""
CALDIM Product Knowledge Domain Models.
Defines products, capabilities, limitations, supported industries,
approved source documents, bounded search chunks, and verified media assets.
"""
import uuid
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class ProductReadinessStatus(models.TextChoices):
    """
    Clear classification of delivery status to prevent premature claims.
    """
    PRODUCTION_READY = "production_ready", "Production Ready"
    PREVIEW_READY = "preview_ready", "Preview / Demo Ready"
    IN_DEVELOPMENT = "in_development", "In Active Development"
    CONCEPT = "concept", "Roadmap Concept"


class ProductPublicationStatus(models.TextChoices):
    """
    Governance status for catalog publication.
    Unverified or draft records are strictly excluded from authoritative AI recommendations.
    """
    PUBLISHED = "published", "Published"
    DRAFT = "draft", "Draft / Unverified"
    ARCHIVED = "archived", "Archived"


class ProductDocumentType(models.TextChoices):
    OFFICIAL_WEBPAGE = "official_webpage", "Official Webpage"
    SPECIFICATION_SHEET = "specification_sheet", "Specification Sheet"
    USER_MANUAL = "user_manual", "User Manual"
    COMPLIANCE_GUIDE = "compliance_guide", "Compliance Guide"


class ProductMediaType(models.TextChoices):
    SCREENSHOT = "screenshot", "Application Screenshot"
    DIAGRAM = "diagram", "Architecture Diagram"
    VIDEO_DEMO = "video_demo", "Video Walkthrough Link"


class Product(models.Model):
    """
    Core CALDIM software module or platform product.
    Supports verified catalogue management and strict governance gating.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=150, help_text="e.g. HR & Payroll Engine, Recruitment Intelligence")
    tagline = models.CharField(max_length=300, blank=True, default="")
    overview = models.TextField(blank=True, default="")

    readiness_status = models.CharField(
        max_length=30,
        choices=ProductReadinessStatus.choices,
        default=ProductReadinessStatus.IN_DEVELOPMENT,
        db_index=True
    )
    publication_status = models.CharField(
        max_length=30,
        choices=ProductPublicationStatus.choices,
        default=ProductPublicationStatus.DRAFT,
        db_index=True,
        help_text="Only published products are included in public consultation"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True only when verified against official CALDIM sources; gates authoritative AI answers"
    )
    verifier_name = models.CharField(max_length=150, blank=True, default="")
    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of latest human/auditor verification against official source"
    )

    customization_scope = models.TextField(
        blank=True,
        default="",
        help_text="Customization capabilities for enterprise client workflows"
    )
    integrations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of supported enterprise integrations, ERPs, and hardware protocols"
    )
    deployment_options = models.JSONField(
        default=list,
        blank=True,
        help_text="Supported deployment options (e.g. Cloud SaaS, Dedicated VPC, On-Premises)"
    )

    verified_source_url = models.URLField(max_length=500, blank=True, default="")
    documentation_url = models.URLField(max_length=500, blank=True, default="")
    demo_url = models.URLField(max_length=500, blank=True, default="")
    video_preview_title = models.CharField(max_length=250, blank=True, default="")
    video_preview_description = models.TextField(blank=True, default="")
    hero_image_url = models.URLField(max_length=500, blank=True, default="")

    pricing_status = models.CharField(
        max_length=150,
        blank=True,
        default="Custom Enterprise Quote",
        help_text="e.g. Custom Enterprise Quote, Per-Employee SaaS, Contact Sales"
    )
    pricing_evidence = models.TextField(
        blank=True,
        default="",
        help_text="Documented pricing policy or verified quotation references"
    )

    case_studies = models.JSONField(
        default=list,
        blank=True,
        help_text="Approved case studies and verified client references"
    )
    customer_references = models.JSONField(
        default=list,
        blank=True,
        help_text="Approved customer references (empty for unverified/confidential)"
    )
    source_references = models.JSONField(
        default=list,
        blank=True,
        help_text="List of source references and provenance metadata"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal verification and governance notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "caldim_products"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="idx_product_slug"),
            models.Index(fields=["readiness_status"], name="idx_product_readiness"),
            models.Index(fields=["publication_status"], name="idx_product_publication"),
            models.Index(fields=["is_active"], name="idx_product_is_active"),
            models.Index(fields=["is_verified"], name="idx_product_is_verified"),
        ]

    def __str__(self):
        v_tag = "Verified" if self.is_verified else "Unverified"
        return f"{self.name} ({self.get_readiness_status_display()} | {v_tag})"


class ProductCapability(models.Model):
    """
    Discrete, source-verified operational capability for a product.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="capabilities")
    title = models.CharField(max_length=200)
    description = models.TextField()
    metric_highlight = models.CharField(
        max_length=250,
        blank=True,
        default="",
        help_text="Verified operational metric (e.g. Zero Spreadsheet Error Margin across 10,000+ Workers)"
    )
    feature_order = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "caldim_product_capabilities"
        ordering = ["product", "feature_order", "title"]

    def __str__(self):
        return f"{self.product.name} — {self.title}"


class ProductLimitation(models.Model):
    """
    Documented boundary, constraint, or non-supported capability to prevent hallucination.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="limitations")
    title = models.CharField(max_length=200)
    description = models.TextField()
    mitigation_or_alternative = models.TextField(
        blank=True,
        default="",
        help_text="Recommended alternative or CALDIM customization service"
    )

    class Meta:
        db_table = "caldim_product_limitations"

    def __str__(self):
        return f"{self.product.name} Limit: {self.title}"


class IndustryProblemMapping(models.Model):
    """
    Maps products to industrial verticals, business pain points, and target buyer personas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="problem_mappings")
    industry = models.CharField(max_length=150, db_index=True)
    business_problem = models.CharField(max_length=250, db_index=True)
    solution_summary = models.TextField()
    target_profession = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="e.g. Plant Operations Manager, Chief Automation Architect"
    )

    class Meta:
        db_table = "caldim_industry_problem_mappings"
        indexes = [
            models.Index(fields=["industry", "business_problem"], name="idx_ind_prob_mapping"),
        ]

    def __str__(self):
        return f"{self.industry}: {self.business_problem} -> {self.product.name}"


class ProductDocument(models.Model):
    """
    Approved source documentation associated with a CALDIM product.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=250)
    source_url = models.URLField(max_length=500)
    document_type = models.CharField(
        max_length=50,
        choices=ProductDocumentType.choices,
        default=ProductDocumentType.OFFICIAL_WEBPAGE
    )
    content_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 digest of raw document text for idempotent change detection"
    )
    version = models.CharField(max_length=50, default="1.0")
    is_approved = models.BooleanField(default=False, db_index=True)
    approved_by = models.CharField(max_length=100, default="CALDIM Product Operations")
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "caldim_product_documents"
        indexes = [
            models.Index(fields=["product", "is_approved"], name="idx_pdoc_approval"),
            models.Index(fields=["content_hash"], name="idx_pdoc_hash"),
        ]

    def __str__(self):
        return f"{self.product.name} — {self.title} (v{self.version})"


class DocumentChunk(models.Model):
    """
    Bounded, searchable chunk with full-text search indexing and document provenance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(ProductDocument, on_delete=models.CASCADE, related_name="chunks")
    section_title = models.CharField(max_length=250, blank=True, default="")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    search_vector = SearchVectorField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Chunk telemetry, token counts, and sanitized flags"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "caldim_document_chunks"
        ordering = ["document", "chunk_index"]
        indexes = [
            GinIndex(fields=["search_vector"], name="idx_dchunk_search_gin"),
            models.Index(fields=["document", "chunk_index"], name="idx_dchunk_doc_idx"),
        ]

    def __str__(self):
        return f"Chunk #{self.chunk_index} ({self.document.product.slug}): {self.section_title or 'Untitled'}"


class ProductMedia(models.Model):
    """
    Approved product screenshots, architecture diagrams, and video walkthrough links.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media_assets")
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=30, choices=ProductMediaType.choices)
    url = models.CharField(max_length=500)
    caption = models.CharField(max_length=300, blank=True, default="")
    is_approved = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "caldim_product_media"
        ordering = ["product", "display_order"]

    def __str__(self):
        return f"{self.product.name} Media: {self.title} ({self.get_media_type_display()})"
