"""
CAPABL Core Package.

Contains all strictly required CAPABL Track 6 components:
- Document Ingestion (PyPDFLoader, RecursiveCharacterTextSplitter)
- RAG & Vector Store (HuggingFace BGE Embeddings, Chroma)
- Core Deterministic Tools (@tool match_tool, @tool calendar_tool)
- Agent Runtime (ChatOllama, create_agent, ReAct loop)
- Streamlit Web Interface
"""

__version__ = "0.1.0"
