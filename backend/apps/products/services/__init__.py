"""
Product knowledge services: ingestion and retrieval.
"""
from apps.products.services.ingestion import KnowledgeIngestionService
from apps.products.services.retrieval import ProductKnowledgeRetrievalService

__all__ = ["KnowledgeIngestionService", "ProductKnowledgeRetrievalService"]
