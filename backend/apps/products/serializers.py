"""
CALDIM Product Knowledge Serializers.
Provides clean representations for product discovery, capabilities, limitations,
and source-attributed search results.
"""
from rest_framework import serializers
from apps.products.models import (
    Product,
    ProductCapability,
    ProductLimitation,
    IndustryProblemMapping,
    ProductMedia,
    ProductDocument,
    DocumentChunk,
)


class ProductCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCapability
        fields = [
            "id",
            "title",
            "description",
            "metric_highlight",
            "feature_order",
            "is_verified",
        ]


class ProductLimitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLimitation
        fields = [
            "id",
            "title",
            "description",
            "mitigation_or_alternative",
        ]


class IndustryProblemMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryProblemMapping
        fields = [
            "id",
            "industry",
            "business_problem",
            "solution_summary",
            "target_profession",
        ]


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = [
            "id",
            "title",
            "media_type",
            "url",
            "caption",
            "display_order",
        ]


class ProductListSerializer(serializers.ModelSerializer):
    readiness_display = serializers.CharField(source="get_readiness_status_display", read_only=True)
    publication_display = serializers.CharField(source="get_publication_status_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "category",
            "tagline",
            "readiness_status",
            "readiness_display",
            "publication_status",
            "publication_display",
            "is_verified",
            "demo_url",
            "video_preview_title",
            "hero_image_url",
            "last_verified_at",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    readiness_display = serializers.CharField(source="get_readiness_status_display", read_only=True)
    publication_display = serializers.CharField(source="get_publication_status_display", read_only=True)
    capabilities = serializers.SerializerMethodField()
    limitations = ProductLimitationSerializer(many=True, read_only=True)
    problem_mappings = IndustryProblemMappingSerializer(many=True, read_only=True)
    media_assets = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "category",
            "tagline",
            "overview",
            "readiness_status",
            "readiness_display",
            "publication_status",
            "publication_display",
            "is_verified",
            "last_verified_at",
            "customization_scope",
            "integrations",
            "deployment_options",
            "verified_source_url",
            "documentation_url",
            "demo_url",
            "video_preview_title",
            "video_preview_description",
            "hero_image_url",
            "pricing_status",
            "pricing_evidence",
            "case_studies",
            "customer_references",
            "capabilities",
            "limitations",
            "problem_mappings",
            "media_assets",
        ]

    def get_capabilities(self, obj):
        request = self.context.get("request")
        is_staff = bool(request and request.user and request.user.is_authenticated and request.user.is_staff)
        if is_staff:
            caps = obj.capabilities.all().order_by("feature_order", "title")
        else:
            caps = obj.capabilities.filter(is_verified=True).order_by("feature_order", "title")
        return ProductCapabilitySerializer(caps, many=True).data

    def get_media_assets(self, obj):
        request = self.context.get("request")
        is_staff = bool(request and request.user and request.user.is_authenticated and request.user.is_staff)
        if is_staff:
            media = obj.media_assets.all().order_by("display_order")
        else:
            media = obj.media_assets.filter(is_approved=True).order_by("display_order")
        return ProductMediaSerializer(media, many=True).data


class SearchSourceSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_slug = serializers.CharField()
    product_name = serializers.CharField()
    readiness_status = serializers.CharField()
    publication_status = serializers.CharField()
    is_verified = serializers.BooleanField()
    document_title = serializers.CharField()
    document_type = serializers.CharField()
    source_url = serializers.URLField()
    version = serializers.CharField()


class DocumentChunkSearchResultSerializer(serializers.Serializer):
    chunk_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    section_title = serializers.CharField(allow_blank=True)
    content = serializers.CharField()
    relevance_score = serializers.FloatField()
    is_untrusted_data = serializers.BooleanField(default=True)
    trust_level = serializers.CharField()
    source = SearchSourceSerializer()
