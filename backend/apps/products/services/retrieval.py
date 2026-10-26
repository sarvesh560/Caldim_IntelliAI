"""
CALDIM Product Knowledge Retrieval Service.
Implements PostgreSQL-native full-text search with GIN index acceleration,
exact provenance attribution, and safe test-runner fallback.
"""
import logging
from typing import List, Dict, Any, Optional

from django.db import connection
from django.db.models import F, Q
from apps.products.models import DocumentChunk, ProductReadinessStatus

logger = logging.getLogger(__name__)


class ProductKnowledgeRetrievalService:
    """
    Search and retrieval interface for CALDIM product knowledge.
    Ensures:
    1. Only approved documents of active products are returned.
    2. Exact source attribution (Product, URL, Section, Chunk index).
    3. High-performance PostgreSQL tsvector / GIN queries.
    4. Seamless fallback for SQLite test environments.
    """

    @classmethod
    def search(
        cls,
        query: str,
        product_slug: Optional[str] = None,
        industry: Optional[str] = None,
        readiness_status: Optional[str] = None,
        require_verified: bool = True,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Execute full-text knowledge retrieval with filtering and provenance.
        require_verified=True guarantees unverified sample content is excluded from AI answers.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        # Base filter: strictly approved documents of active products
        base_qs = DocumentChunk.objects.filter(
            document__is_approved=True,
            document__product__is_active=True,
        ).select_related("document", "document__product")

        # Authoritative recommendation guard: strictly require verified and published products
        if require_verified:
            base_qs = base_qs.filter(
                document__product__is_verified=True,
                document__product__publication_status="published",
            )

        if product_slug:
            base_qs = base_qs.filter(document__product__slug=product_slug)

        if readiness_status:
            base_qs = base_qs.filter(document__product__readiness_status=readiness_status)

        if industry:
            base_qs = base_qs.filter(
                document__product__problem_mappings__industry__iexact=industry
            ).distinct()

        # Database engine branch
        if connection.vendor == "postgresql":
            return cls._search_postgresql(base_qs, clean_query, limit)
        else:
            return cls._search_fallback(base_qs, clean_query, limit)

    @classmethod
    def _search_postgresql(
        cls,
        queryset,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL native full-text search using tsquery and SearchRank.
        """
        from django.contrib.postgres.search import SearchQuery, SearchRank

        # Websearch query parser handles quoted phrases, +, - naturally
        try:
            search_query = SearchQuery(query, config="english", search_type="websearch")
            ranked_qs = queryset.annotate(
                rank=SearchRank(F("search_vector"), search_query)
            ).filter(search_vector=search_query).order_by("-rank")[:limit]

            results = []
            for chunk in ranked_qs:
                results.append(cls._format_result_item(chunk, score=float(chunk.rank)))
            return results
        except Exception as e:
            logger.warning("PostgreSQL websearch query failed (%s), falling back to plain: %s", query, e)
            search_query = SearchQuery(query, config="english", search_type="plain")
            ranked_qs = queryset.annotate(
                rank=SearchRank(F("search_vector"), search_query)
            ).filter(search_vector=search_query).order_by("-rank")[:limit]

            results = []
            for chunk in ranked_qs:
                results.append(cls._format_result_item(chunk, score=float(chunk.rank)))
            return results

    @classmethod
    def _search_fallback(
        cls,
        queryset,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Fallback search for SQLite test runner using multi-term icontains.
        """
        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []

        q_obj = Q()
        for term in terms:
            q_obj |= Q(content__icontains=term) | Q(section_title__icontains=term)

        matches = queryset.filter(q_obj)[: limit * 2]

        # Basic score calculation by keyword occurrences
        scored = []
        for chunk in matches:
            content_lower = chunk.content.lower()
            title_lower = chunk.section_title.lower()
            score = 0.0
            for t in terms:
                t_lower = t.lower()
                score += content_lower.count(t_lower) * 0.1
                score += title_lower.count(t_lower) * 0.3
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:limit]:
            results.append(cls._format_result_item(chunk, score=round(score, 3)))

        return results

    @staticmethod
    def _format_result_item(chunk: DocumentChunk, score: float) -> Dict[str, Any]:
        """
        Formats retrieved chunk with complete source provenance and metadata.
        Explicitly flags content as untrusted data for LLM prompt boundaries.
        """
        product = chunk.document.product
        is_authoritative = bool(product.is_verified and product.publication_status == "published")
        return {
            "chunk_id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "section_title": chunk.section_title,
            "content": chunk.content,
            "relevance_score": score,
            "is_untrusted_data": True,  # Prompt builders must encapsulate inside inert boundary tags
            "trust_level": "verified_authoritative" if is_authoritative else "unverified_draft",
            "source": {
                "product_id": str(product.id),
                "product_slug": product.slug,
                "product_name": product.name,
                "readiness_status": product.readiness_status,
                "publication_status": product.publication_status,
                "is_verified": product.is_verified,
                "document_title": chunk.document.title,
                "document_type": chunk.document.document_type,
                "source_url": chunk.document.source_url,
                "version": chunk.document.version,
            },
        }
