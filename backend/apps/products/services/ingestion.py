"""
CALDIM Product Knowledge Ingestion Service.
Provides safe, bounded, idempotent ingestion of verified product documents with
provenance tracking, prompt-injection defense, and full-text search indexing.
"""
import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse

from django.db import transaction, connection
from django.utils import timezone
from apps.products.models import (
    Product,
    ProductDocument,
    DocumentChunk,
    ProductDocumentType,
)

logger = logging.getLogger(__name__)

# Approved domains for authoritative CALDIM documentation
APPROVED_DOMAINS = {
    "caldimproducts.com",
    "www.caldimproducts.com",
    "caldim.com",
    "www.caldim.com",
    "docs.caldim.com",
    "internal.caldim.com",
    "localhost",
    "127.0.0.1",
}

# Prompt injection regex patterns to detect and neutralize adversarial content
INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)\b",
    r"(?i)\byou\s+are\s+now\s+(a|an|in)\b",
    r"(?i)\bsystem\s*:\s*",
    r"(?i)\b(system\s+prompt|developer\s+mode|jailbreak|dan\s+mode)\b",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)<\|endoftext\|>",
    r"(?i)</?system>",
]

COMPILED_INJECTION_RE = [re.compile(p) for p in INJECTION_PATTERNS]


class KnowledgeIngestionService:
    """
    Handles validation, sanitization, bounded chunking, and idempotent storage
    of CALDIM product knowledge documents.
    """

    @staticmethod
    def validate_source_url(url: str) -> bool:
        """
        Ensure the document source URL originates from an approved domain
        or local verification fixture.
        """
        if not url:
            return False
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False
            return hostname.lower() in APPROVED_DOMAINS
        except Exception as e:
            logger.warning("Failed to parse source URL %s: %s", url, e)
            return False

    @staticmethod
    def neutralize_prompt_injection(raw_text: str) -> Tuple[str, bool, List[str]]:
        """
        Detects adversarial directives that attempt to hijack LLM behavior.
        Neutralizes detected directives by prefixing and tagging them as inert quotation.
        Returns (sanitized_text, was_injection_detected, matched_patterns).
        """
        detected_patterns = []
        sanitized_text = raw_text

        for pattern in COMPILED_INJECTION_RE:
            matches = pattern.findall(sanitized_text)
            if matches:
                detected_patterns.append(pattern.pattern)
                # Neutralize by replacing with an inert neutralized marker
                sanitized_text = pattern.sub("[NEUTRALIZED_UNAUTHORIZED_DIRECTIVE]", sanitized_text)

        was_detected = len(detected_patterns) > 0
        if was_detected:
            logger.warning(
                "Adversarial prompt injection pattern detected and neutralized. Patterns: %s",
                detected_patterns,
            )

        return sanitized_text, was_detected, detected_patterns

    @staticmethod
    def chunk_document(
        text: str,
        section_title: str = "",
        max_chunk_chars: int = 1200,
        chunk_overlap: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        Splits sanitized document text into bounded, coherent paragraph chunks.
        Respects section headings and paragraph boundaries where possible.
        """
        if not text or not text.strip():
            return []

        # Split into double-newline paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_length = 0

        for p in paragraphs:
            # If paragraph itself is excessively large, split by sentences
            if len(p) > max_chunk_chars:
                sentences = re.split(r"(?<=[.!?])\s+", p)
                for s in sentences:
                    if current_length + len(s) > max_chunk_chars and current_chunk:
                        chunk_body = " ".join(current_chunk).strip()
                        chunks.append(chunk_body)
                        # Overlap: keep last piece if reasonable
                        if chunk_overlap > 0 and len(current_chunk[-1]) < chunk_overlap:
                            current_chunk = [current_chunk[-1], s]
                            current_length = len(current_chunk[0]) + len(s) + 1
                        else:
                            current_chunk = [s]
                            current_length = len(s)
                    else:
                        current_chunk.append(s)
                        current_length += len(s) + 1
            else:
                if current_length + len(p) > max_chunk_chars and current_chunk:
                    chunk_body = "\n\n".join(current_chunk).strip()
                    chunks.append(chunk_body)
                    current_chunk = [p]
                    current_length = len(p)
                else:
                    current_chunk.append(p)
                    current_length += len(p) + 2

        if current_chunk:
            chunk_body = "\n\n".join(current_chunk).strip()
            chunks.append(chunk_body)

        formatted_chunks = []
        for idx, body in enumerate(chunks, start=1):
            formatted_chunks.append({
                "chunk_index": idx,
                "section_title": section_title,
                "content": body,
                "char_count": len(body),
                "word_count": len(body.split()),
            })

        return formatted_chunks

    @classmethod
    @transaction.atomic
    def ingest_document(
        cls,
        product: Product,
        title: str,
        source_url: str,
        raw_text: str,
        document_type: str = ProductDocumentType.OFFICIAL_WEBPAGE,
        version: str = "1.0",
        approved_by: str = "CALDIM Product Operations",
        is_approved: bool = True,
        section_title: str = "",
        force_reingest: bool = False,
    ) -> Dict[str, Any]:
        """
        Idempotently ingest a product document:
        1. Validate source URL.
        2. Neutralize prompt-injection directives.
        3. Compute SHA-256 hash.
        4. Check for duplicate/unchanged content (skip if identical and not forced).
        5. Create/update ProductDocument and bounded DocumentChunks.
        6. Update PostgreSQL search_vector on chunks.
        """
        # 1. URL validation
        if not cls.validate_source_url(source_url):
            raise ValueError(
                f"Source URL '{source_url}' is not from an approved CALDIM domain."
            )

        # 2. Prompt injection defense
        sanitized_text, injection_detected, patterns = cls.neutralize_prompt_injection(raw_text)

        # 3. Content hash
        content_hash = hashlib.sha256(sanitized_text.encode("utf-8")).hexdigest()

        # 4. Check existing document for idempotency
        existing_doc = ProductDocument.objects.filter(
            product=product,
            source_url=source_url,
        ).first()

        if existing_doc and existing_doc.content_hash == content_hash and not force_reingest:
            chunk_count = existing_doc.chunks.count()
            if chunk_count > 0:
                logger.info(
                    "Document '%s' is up to date (hash %s matches). Skipping re-chunking.",
                    title,
                    content_hash[:8],
                )
                return {
                    "document_id": str(existing_doc.id),
                    "product_slug": product.slug,
                    "action": "skipped_unchanged",
                    "content_hash": content_hash,
                    "chunk_count": chunk_count,
                    "injection_detected": injection_detected,
                }

        # 5. Save or update ProductDocument
        if existing_doc:
            doc = existing_doc
            doc.title = title
            doc.document_type = document_type
            doc.content_hash = content_hash
            doc.version = version
            doc.approved_by = approved_by
            doc.is_approved = is_approved
            doc.save()
            # Clear obsolete chunks for clean atomic replacement
            doc.chunks.all().delete()
            action = "updated"
        else:
            doc = ProductDocument.objects.create(
                product=product,
                title=title,
                source_url=source_url,
                document_type=document_type,
                content_hash=content_hash,
                version=version,
                approved_by=approved_by,
                is_approved=is_approved,
            )
            action = "created"

        # 6. Chunk text and persist chunks
        chunk_dicts = cls.chunk_document(
            text=sanitized_text,
            section_title=section_title or title,
        )

        chunk_instances = []
        for c in chunk_dicts:
            meta = {
                "char_count": c["char_count"],
                "word_count": c["word_count"],
                "injection_detected": injection_detected,
                "sanitized_patterns": patterns,
                "ingested_timestamp": timezone.now().isoformat(),
            }
            chunk_inst = DocumentChunk(
                document=doc,
                chunk_index=c["chunk_index"],
                section_title=c["section_title"],
                content=c["content"],
                metadata=meta,
            )
            chunk_instances.append(chunk_inst)

        DocumentChunk.objects.bulk_create(chunk_instances)

        # 7. Update PostgreSQL full-text search vector if on PostgreSQL
        cls.update_search_vectors_for_document(doc)

        logger.info(
            "Document '%s' successfully ingested into %d chunks (action: %s).",
            title,
            len(chunk_instances),
            action,
        )

        return {
            "document_id": str(doc.id),
            "product_slug": product.slug,
            "action": action,
            "content_hash": content_hash,
            "chunk_count": len(chunk_instances),
            "injection_detected": injection_detected,
        }

    @classmethod
    def update_search_vectors_for_document(cls, document: ProductDocument) -> None:
        """
        Updates the tsvector search_vector column using PostgreSQL's SearchVector.
        Gracefully skips when running on SQLite in-memory test runner.
        """
        if connection.vendor != "postgresql":
            return

        from django.contrib.postgres.search import SearchVector

        # Weight A for section_title, Weight B for chunk content
        DocumentChunk.objects.filter(document=document).update(
            search_vector=(
                SearchVector("section_title", weight="A", config="english")
                + SearchVector("content", weight="B", config="english")
            )
        )
