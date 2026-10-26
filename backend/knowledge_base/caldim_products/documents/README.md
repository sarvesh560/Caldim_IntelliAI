# CALDIM Product Knowledge — Documents Directory

This directory stores approved source documentation, specification sheets, user manuals, and compliance guides associated with CALDIM products.

## File Organization Guidelines

1. **File Naming Convention**:
   - `<product_slug>_spec.md`: Formal specification sheets.
   - `<product_slug>_manual.md`: User and operational manuals.
   - `<product_slug>_compliance.md`: Statutory and regulatory compliance briefs.

2. **Provenance & Ingestion Requirements**:
   - Every document must cite its authoritative source (e.g., official URL, document version, and author).
   - Documents are ingested into the database as bounded text chunks (`DocumentChunk`) with SHA-256 hash detection.
   - The ingestion pipeline automatically neutralizes any prompt-injection directives (e.g. `IGNORE INSTRUCTIONS` or `SYSTEM:`).
   - Ingestion updates the PostgreSQL native full-text search vector (`search_vector`) with GIN index acceleration.

3. **Status Gating**:
   - Only documents marked `is_approved = true` belonging to products with `is_verified = true` and `publication_status = "published"` are accessible by the AI consultation engine for authoritative recommendations.
