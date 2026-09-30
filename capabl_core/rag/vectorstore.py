"""
Chroma Vector Store Subsystem.

CAPABL Requirement:
- Chroma as primary and only vector database.
- Persistent storage with configurable persistence directory.
- Reusable vector store surviving application restarts.
- Full metadata support (document_type, document_id, source, page, candidate_id, chunk_index).
- Deterministic collection configuration.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

from capabl_core.rag.embeddings import get_embedding_function


class ChromaVectorStoreManager:
    """Manages Chroma vector database persistence, collections, and document indexing."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_function: Optional[Embeddings] = None,
    ):
        """
        Initializes the Chroma vector store manager.

        Args:
            persist_directory: Path to on-disk directory for Chroma SQLite/index files.
            collection_name: Unique collection name in Chroma.
            embedding_function: LangChain Embeddings instance.
        """
        if not persist_directory:
            try:
                from capabl_core.config.settings import get_settings
                self.persist_directory = get_settings().chroma_persist_directory
            except Exception:
                self.persist_directory = str(Path(os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")).resolve())
        else:
            self.persist_directory = str(Path(persist_directory).resolve())

        if not collection_name:
            try:
                from capabl_core.config.settings import get_settings
                self.collection_name = get_settings().chroma_collection_name
            except Exception:
                self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "recruitment_documents").strip()
        else:
            self.collection_name = collection_name.strip()
        self._embedding_function = embedding_function
        self._vectorstore: Optional[Chroma] = None

    @property
    def embedding_function(self) -> Embeddings:
        """Lazily resolves the embedding function if not explicitly injected."""
        if self._embedding_function is None:
            self._embedding_function = get_embedding_function()
        return self._embedding_function

    def get_or_create_store(self) -> Chroma:
        """
        Initializes or connects to the persistent Chroma store.
        Survives application restarts.
        """
        if self._vectorstore is not None:
            return self._vectorstore

        # Ensure persistence directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self._vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory,
        )
        return self._vectorstore

    def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None) -> List[str]:
        """
        Indexes documents into the Chroma collection, preserving all metadata.

        Args:
            documents: List of chunked Document objects with metadata.
            ids: Optional custom vector IDs.

        Returns:
            List[str]: List of inserted document IDs.
        """
        if not documents:
            return []

        store = self.get_or_create_store()

        # Sanitize metadata values for Chroma (Chroma accepts str, int, float, bool)
        sanitized_docs: List[Document] = []
        for doc in documents:
            clean_meta: Dict[str, Any] = {}
            for k, v in doc.metadata.items():
                if v is not None:
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)
            sanitized_docs.append(
                Document(page_content=doc.page_content, metadata=clean_meta)
            )

        return store.add_documents(documents=sanitized_docs, ids=ids)

    # Alias for indexing
    index_documents = add_documents

    def count(self) -> int:
        """Returns the total number of indexed vectors in the collection."""
        store = self.get_or_create_store()
        try:
            return store._collection.count()
        except Exception:
            return 0

    def delete_documents(self, where: Dict[str, Any]) -> int:
        """
        Deletes documents matching a metadata filter without affecting other documents.
        
        Args:
            where: Metadata filter dict (e.g., {"candidate_id": "alex_chen", "document_type": "resume"}).
            
        Returns:
            int: Number of deleted document chunks.
        """
        if not where:
            return 0
        store = self.get_or_create_store()
        try:
            matched = store._collection.get(where=where)
            ids_to_delete = matched.get("ids", [])
            if ids_to_delete:
                store._collection.delete(ids=ids_to_delete)
                return len(ids_to_delete)
            return 0
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Error deleting documents matching {where}: {exc}")
            return 0

    def delete_collection(self) -> None:
        """Deletes the active collection and resets state."""
        store = self.get_or_create_store()
        try:
            store.delete_collection()
        finally:
            self._vectorstore = None

