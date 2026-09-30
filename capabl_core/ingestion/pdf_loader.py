"""
PDF Ingestion & Document-Specific Chunking Pipeline.

CAPABL Requirement:
- PyPDFLoader for extracting raw text and page-level metadata from PDF documents.
- RecursiveCharacterTextSplitter for document-specific chunking.
- Explicit document types: 'resume', 'job_description', 'policy'.
- Metadata invariance: document_type, document_id, source, page, (optional) candidate_id
  must survive from PDF to Retriever.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentType(str, Enum):
    """Allowed document categories in the Recruitment Intelligence Agent."""
    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"
    POLICY = "policy"


class DocumentMetadata(BaseModel):
    """Strict metadata schema enforced across all ingested documents and chunks."""
    document_type: DocumentType = Field(..., description="Explicit document classification")
    document_id: str = Field(..., description="Unique persistent identifier for the document")
    source: str = Field(..., description="File path or URI of source document")
    page: int = Field(..., ge=0, description="Page number within source document (0-indexed)")
    candidate_id: Optional[str] = Field(default=None, description="Candidate identifier if document_type is resume")
    chunk_index: Optional[int] = Field(default=None, description="Sequential chunk index within document")


class ChunkingProfile:
    """Document-specific chunk sizing and overlap parameters."""
    PROFILES: Dict[DocumentType, Dict[str, int]] = {
        # Resumes: Smaller chunks preserve individual roles/skills without bleeding across sections
        DocumentType.RESUME: {"chunk_size": 600, "chunk_overlap": 100},
        # Job Descriptions: Sized to keep discrete requirement/responsibility blocks intact
        DocumentType.JOB_DESCRIPTION: {"chunk_size": 500, "chunk_overlap": 80},
        # Policies: Larger chunks retain complete legal/procedural clauses and paragraphs
        DocumentType.POLICY: {"chunk_size": 800, "chunk_overlap": 150},
    }

    @classmethod
    def get_params(cls, doc_type: DocumentType) -> Dict[str, int]:
        return cls.PROFILES.get(doc_type, {"chunk_size": 600, "chunk_overlap": 100})


class PDFIngestionPipeline:
    """Ingests PDF documents, tags metadata, and performs document-specific chunking."""

    @staticmethod
    def _resolve_document_type(doc_type: Union[DocumentType, str]) -> DocumentType:
        if isinstance(doc_type, DocumentType):
            return doc_type
        clean_str = str(doc_type).strip().lower()
        try:
            return DocumentType(clean_str)
        except ValueError as exc:
            valid_types = [t.value for t in DocumentType]
            raise ValueError(
                f"Invalid document_type '{doc_type}'. Allowed types are: {valid_types}. "
                f"Document type must be assigned explicitly."
            ) from exc

    def load_pdf(
        self,
        file_path: Union[str, Path],
        document_type: Union[DocumentType, str],
        document_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        source_override: Optional[str] = None,
    ) -> List[Document]:
        """
        Loads a PDF file using PyPDFLoader and attaches validated metadata.

        Args:
            file_path: Path to the PDF file.
            document_type: 'resume', 'job_description', or 'policy'.
            document_id: Optional unique identifier (defaults to file stem).
            candidate_id: Optional candidate ID (only attached if document_type is resume).
            source_override: Optional human-readable source/filename override.

        Returns:
            List[Document]: List of LangChain Document objects representing pages.
        """
        resolved_path = Path(file_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"PDF file not found at path: {resolved_path}")
        if resolved_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, received: {resolved_path.name}")

        resolved_type = self._resolve_document_type(document_type)
        doc_id = (document_id or resolved_path.stem).strip()

        loader = PyPDFLoader(str(resolved_path))
        loaded_pages = loader.load()

        if not loaded_pages:
            raise ValueError(f"No text pages could be loaded from PDF: {resolved_path.name}")

        normalized_docs: List[Document] = []
        for idx, page_doc in enumerate(loaded_pages):
            page_number = int(page_doc.metadata.get("page", idx))

            # Build metadata conforming strictly to specification
            meta: Dict[str, Any] = {
                "document_type": resolved_type.value,
                "document_id": doc_id,
                "source": source_override or str(resolved_path),
                "page": page_number,
            }

            # Attach candidate_id only if provided and appropriate
            if resolved_type == DocumentType.RESUME and candidate_id:
                meta["candidate_id"] = candidate_id.strip()

            # Validate against Pydantic schema
            DocumentMetadata(**meta)

            normalized_docs.append(
                Document(page_content=page_doc.page_content, metadata=meta)
            )

        return normalized_docs

    def chunk_documents(
        self,
        documents: List[Document],
        document_type: Optional[Union[DocumentType, str]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Document]:
        """
        Splits documents using RecursiveCharacterTextSplitter with document-type-specific sizing.
        Preserves all metadata across chunks and assigns chunk_index.
        """
        if not documents:
            return []

        # Determine document type from parameter or first document's metadata
        if document_type is not None:
            resolved_type = self._resolve_document_type(document_type)
        else:
            first_meta_type = documents[0].metadata.get("document_type")
            if not first_meta_type:
                raise ValueError("Document metadata missing 'document_type' and none provided to chunk_documents.")
            resolved_type = self._resolve_document_type(first_meta_type)

        profile = ChunkingProfile.get_params(resolved_type)
        size = chunk_size or profile["chunk_size"]
        overlap = chunk_overlap or profile["chunk_overlap"]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        all_chunks: List[Document] = []
        for doc in documents:
            sub_chunks = splitter.split_documents([doc])
            for chunk_idx, chunk in enumerate(sub_chunks):
                # Ensure all metadata survived
                chunk.metadata["document_type"] = resolved_type.value
                chunk.metadata["chunk_index"] = chunk_idx
                # Validate with Pydantic
                DocumentMetadata(**chunk.metadata)
                all_chunks.append(chunk)

        return all_chunks

    def load_and_chunk_pdf(
        self,
        file_path: Union[str, Path],
        document_type: Union[DocumentType, str],
        document_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        source_override: Optional[str] = None,
    ) -> List[Document]:
        """
        Convenience method loading a PDF and immediately applying document-specific chunking.
        """
        raw_docs = self.load_pdf(
            file_path=file_path,
            document_type=document_type,
            document_id=document_id,
            candidate_id=candidate_id,
            source_override=source_override,
        )
        return self.chunk_documents(
            documents=raw_docs,
            document_type=document_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


