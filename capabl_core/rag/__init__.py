"""
RAG Subsystem Package.

Exposes:
- get_embedding_function
- ChromaVectorStoreManager
- RecruitmentRetriever
"""

from capabl_core.rag.embeddings import get_embedding_function
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever

__all__ = [
    "get_embedding_function",
    "ChromaVectorStoreManager",
    "RecruitmentRetriever",
]
