"""
CALDIM Product Knowledge API Views.
Exposes public discovery and search endpoints while maintaining strict boundary
isolation for internal/unapproved records and administrative data.
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.throttling import ScopedRateThrottle

from apps.products.models import (
    Product,
    ProductReadinessStatus,
    ProductPublicationStatus,
)
from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    DocumentChunkSearchResultSerializer,
)
from apps.products.services.retrieval import ProductKnowledgeRetrievalService

logger = logging.getLogger(__name__)


class ProductListView(APIView):
    """
    GET /api/v1/products/
    Public discovery endpoint listing active, verified, published CALDIM products.
    Staff users can optionally preview unverified/draft products via ?include_drafts=true.
    Supports filtering by readiness_status, category, and industry vertical.
    """
    permission_classes = []

    def get(self, request, *args, **kwargs):
        is_staff = bool(request.user and request.user.is_authenticated and request.user.is_staff)
        include_drafts = is_staff and request.query_params.get("include_drafts", "").lower() in ("true", "1")

        if include_drafts:
            queryset = Product.objects.filter(is_active=True)
        else:
            queryset = Product.objects.filter(
                is_active=True,
                is_verified=True,
                publication_status=ProductPublicationStatus.PUBLISHED,
            )

        readiness = request.query_params.get("readiness", "").strip()
        if readiness:
            queryset = queryset.filter(readiness_status=readiness)

        category = request.query_params.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__icontains=category)

        industry = request.query_params.get("industry", "").strip()
        if industry:
            queryset = queryset.filter(
                problem_mappings__industry__iexact=industry
            ).distinct()

        serializer = ProductListSerializer(queryset, many=True)
        return Response(
            {
                "count": queryset.count(),
                "products": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ProductDetailView(APIView):
    """
    GET /api/v1/products/<slug>/
    Retrieve comprehensive, verified product profile including capabilities,
    documented limitations, industry problem mappings, and media assets.
    Public callers can ONLY access verified, published products; draft or unverified
    records return HTTP 404 Not Found.
    Staff users are authorized to preview unverified/draft products.
    """
    permission_classes = []

    def get(self, request, slug, *args, **kwargs):
        is_staff = bool(request.user and request.user.is_authenticated and request.user.is_staff)

        base_qs = Product.objects.prefetch_related(
            "capabilities",
            "limitations",
            "problem_mappings",
            "media_assets",
        ).filter(is_active=True)

        if not is_staff:
            base_qs = base_qs.filter(
                is_verified=True,
                publication_status=ProductPublicationStatus.PUBLISHED,
            )

        product = get_object_or_404(base_qs, slug=slug)

        serializer = ProductDetailSerializer(product, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductSearchView(APIView):
    """
    GET /api/v1/products/search/?q=<query>&product=<slug>&industry=<industry>&readiness=<status>
    High-performance, source-attributed search across approved product knowledge chunks.
    Protected by rate throttling to prevent query exhaustion attacks.
    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_search"

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Query parameter 'q' must contain at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_slug = request.query_params.get("product", "").strip() or None
        industry = request.query_params.get("industry", "").strip() or None
        readiness = request.query_params.get("readiness", "").strip() or None

        try:
            limit = int(request.query_params.get("limit", 10))
            limit = max(1, min(limit, 25))
        except ValueError:
            limit = 10

        # Public search strictly enforces require_verified=True; no client parameter can bypass this
        results = ProductKnowledgeRetrievalService.search(
            query=query,
            product_slug=product_slug,
            industry=industry,
            readiness_status=readiness,
            require_verified=True,
            limit=limit,
        )

        serializer = DocumentChunkSearchResultSerializer(results, many=True)
        return Response(
            {
                "query": query,
                "count": len(results),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class StaffProductPreviewSearchView(APIView):
    """
    GET /api/v1/products/staff-search/?q=<query>&product=<slug>&industry=<industry>&readiness=<status>
    Protected internal search endpoint strictly for authenticated staff/admin users.
    Allows previewing unverified draft product documentation chunks during internal review.
    """
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_search"

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Query parameter 'q' must contain at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_slug = request.query_params.get("product", "").strip() or None
        industry = request.query_params.get("industry", "").strip() or None
        readiness = request.query_params.get("readiness", "").strip() or None

        try:
            limit = int(request.query_params.get("limit", 10))
            limit = max(1, min(limit, 25))
        except ValueError:
            limit = 10

        results = ProductKnowledgeRetrievalService.search(
            query=query,
            product_slug=product_slug,
            industry=industry,
            readiness_status=readiness,
            require_verified=False,
            limit=limit,
        )

        serializer = DocumentChunkSearchResultSerializer(results, many=True)
        return Response(
            {
                "query": query,
                "count": len(results),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ProductReadinessView(APIView):
    """
    GET /api/v1/products/readiness/
    Provides structured readiness inventory to ensure transparent and truthful
    solution recommendations without claiming unverified or conceptual features.
    Public callers only receive verified, published products.
    """
    permission_classes = []

    def get(self, request, *args, **kwargs):
        is_staff = bool(request.user and request.user.is_authenticated and request.user.is_staff)
        if is_staff:
            active_products = Product.objects.filter(is_active=True).order_by("name")
        else:
            active_products = Product.objects.filter(
                is_active=True,
                is_verified=True,
                publication_status=ProductPublicationStatus.PUBLISHED,
            ).order_by("name")

        grouped = {
            status_choice[0]: {
                "display": status_choice[1],
                "count": 0,
                "products": [],
            }
            for status_choice in ProductReadinessStatus.choices
        }

        for p in active_products:
            st = p.readiness_status
            if st in grouped:
                grouped[st]["count"] += 1
                grouped[st]["products"].append({
                    "id": str(p.id),
                    "slug": p.slug,
                    "name": p.name,
                    "category": p.category,
                    "verified_source_url": p.verified_source_url,
                    "has_demo": bool(p.demo_url),
                })

        return Response(
            {
                "total_active_products": active_products.count(),
                "inventory": grouped,
            },
            status=status.HTTP_200_OK,
        )
