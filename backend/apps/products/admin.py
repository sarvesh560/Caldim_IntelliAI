"""
CALDIM Product Knowledge Django Admin Interface.
Provides administrative controls for product records, readiness states,
source documents, bounded search chunks, and verified media assets.
"""
from django.contrib import admin
from django.utils import timezone
from apps.products.models import (
    Product,
    ProductCapability,
    ProductLimitation,
    IndustryProblemMapping,
    ProductDocument,
    DocumentChunk,
    ProductMedia,
    ProductReadinessStatus,
)


class ProductCapabilityInline(admin.TabularInline):
    model = ProductCapability
    extra = 1
    fields = ("title", "description", "metric_highlight", "feature_order", "is_verified")


class ProductLimitationInline(admin.TabularInline):
    model = ProductLimitation
    extra = 1
    fields = ("title", "description", "mitigation_or_alternative")


class IndustryProblemMappingInline(admin.TabularInline):
    model = IndustryProblemMapping
    extra = 1
    fields = ("industry", "business_problem", "solution_summary", "target_profession")


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ("title", "media_type", "url", "caption", "is_approved", "display_order")


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 0
    fields = ("title", "document_type", "version", "source_url", "is_approved", "approved_by")
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "category",
        "readiness_status",
        "is_active",
        "last_verified_at",
        "created_at",
    )
    list_filter = ("readiness_status", "is_active", "category")
    search_fields = ("name", "slug", "category", "tagline", "overview")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        ProductCapabilityInline,
        ProductLimitationInline,
        IndustryProblemMappingInline,
        ProductMediaInline,
        ProductDocumentInline,
    ]
    actions = [
        "mark_verified_now",
        "set_production_ready",
        "set_preview_ready",
        "set_in_development",
        "activate_products",
        "deactivate_products",
    ]

    @admin.action(description="Mark selected products as verified against official sources now")
    def mark_verified_now(self, request, queryset):
        queryset.update(last_verified_at=timezone.now())

    @admin.action(description="Set readiness status to Production Ready")
    def set_production_ready(self, request, queryset):
        queryset.update(readiness_status=ProductReadinessStatus.PRODUCTION_READY)

    @admin.action(description="Set readiness status to Preview Ready")
    def set_preview_ready(self, request, queryset):
        queryset.update(readiness_status=ProductReadinessStatus.PREVIEW_READY)

    @admin.action(description="Set readiness status to In Development")
    def set_in_development(self, request, queryset):
        queryset.update(readiness_status=ProductReadinessStatus.IN_DEVELOPMENT)

    @admin.action(description="Activate selected products")
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected products")
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ("chunk_index", "section_title", "content", "created_at")
    readonly_fields = ("created_at",)
    can_delete = True


@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "document_type",
        "version",
        "is_approved",
        "approved_by",
        "ingested_at",
    )
    list_filter = ("is_approved", "document_type", "product")
    search_fields = ("title", "source_url", "content_hash", "approved_by")
    inlines = [DocumentChunkInline]
    actions = ["approve_documents", "revoke_approval"]

    @admin.action(description="Approve selected source documents for consultation retrieval")
    def approve_documents(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Revoke approval for selected documents")
    def revoke_approval(self, request, queryset):
        queryset.update(is_approved=False)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("__str__", "document", "chunk_index", "section_title", "created_at")
    list_filter = ("document__product", "document__is_approved")
    search_fields = ("content", "section_title")
    readonly_fields = ("search_vector", "created_at")


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "media_type", "is_approved", "display_order")
    list_filter = ("media_type", "is_approved", "product")
    search_fields = ("title", "caption", "url")
    actions = ["approve_media", "revoke_media"]

    @admin.action(description="Approve selected media assets")
    def approve_media(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Revoke approval for selected media assets")
    def revoke_media(self, request, queryset):
        queryset.update(is_approved=False)
