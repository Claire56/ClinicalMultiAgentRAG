"""Pinecone service for vector storage and retrieval."""
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class PineconeService:
    """Service for Pinecone vector database operations."""
    
    def __init__(self):
        """Initialize Pinecone service."""
        if not settings.PINECONE_API_KEY:
            logger.warning("Pinecone API key not set. Vector search will be unavailable.")
            self.pinecone = None
            self.index = None
            self.vector_store = None
            self.embeddings = None
            return
        
        try:
            # Initialize Pinecone
            self.pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Initialize embeddings (using OpenAI by default, can be configured)
            if settings.OPENAI_API_KEY:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model="text-embedding-3-small",  # Cost-effective embedding model
                )
            else:
                logger.warning("OpenAI API key not set. Embeddings will be unavailable.")
                self.embeddings = None
            
            # Get or create index
            self._initialize_index()
            
            # Initialize vector store
            if self.index and self.embeddings:
                self.vector_store = PineconeVectorStore(
                    index=self.index,
                    embedding=self.embeddings,
                )
            
            logger.info(
                "Pinecone initialized",
                index_name=settings.PINECONE_INDEX_NAME,
                environment=settings.PINECONE_ENVIRONMENT,
            )
        except Exception as e:
            logger.error("Failed to initialize Pinecone", error=str(e))
            self.pinecone = None
            self.index = None
            self.vector_store = None
    
    def _initialize_index(self):
        """Initialize or create Pinecone index."""
        try:
            # Check if index exists
            existing_indexes = [idx.name for idx in self.pinecone.list_indexes()]
            
            if settings.PINECONE_INDEX_NAME in existing_indexes:
                self.index = self.pinecone.Index(settings.PINECONE_INDEX_NAME)
                logger.info("Using existing Pinecone index", index_name=settings.PINECONE_INDEX_NAME)
            else:
                # Create new index
                logger.info("Creating new Pinecone index", index_name=settings.PINECONE_INDEX_NAME)
                self.pinecone.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=1536,  # OpenAI text-embedding-3-small dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT,
                    ),
                )
                self.index = self.pinecone.Index(settings.PINECONE_INDEX_NAME)
                logger.info("Pinecone index created", index_name=settings.PINECONE_INDEX_NAME)
        except Exception as e:
            logger.error("Failed to initialize Pinecone index", error=str(e))
            self.index = None
    
    async def add_documents(
        self,
        documents: List[Document],
        namespace: Optional[str] = None,
    ) -> List[str]:
        """Add documents to Pinecone index."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        try:
            ids = await self.vector_store.aadd_documents(documents)
            logger.info(
                "Documents added to Pinecone",
                count=len(documents),
                namespace=namespace,
            )
            return ids
        except Exception as e:
            logger.error("Failed to add documents to Pinecone", error=str(e))
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Perform similarity search in Pinecone."""
        if not self.vector_store:
            logger.warning("Vector store not initialized. Returning empty results.")
            return []
        
        try:
            results = await self.vector_store.asimilarity_search(
                query,
                k=k,
                namespace=namespace,
                filter=filter,
            )
            logger.info(
                "Similarity search completed",
                query=query[:50],
                results_count=len(results),
            )
            return results
        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            return []
    
    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """Perform similarity search with scores."""
        if not self.vector_store:
            return []
        
        try:
            results = await self.vector_store.asimilarity_search_with_score(
                query,
                k=k,
                namespace=namespace,
                filter=filter,
            )
            return results
        except Exception as e:
            logger.error("Similarity search with score failed", error=str(e))
            return []
    
    def get_llm(self, model_name: Optional[str] = None, temperature: float = 0.0):
        """Get LLM instance based on configured provider."""
        if settings.LLM_PROVIDER == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("Anthropic API key not set")
            return ChatAnthropic(
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                model_name=model_name or "claude-3-5-sonnet-20241022",
                temperature=temperature,
            )
        else:  # Default to OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not set")
            return ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model_name=model_name or "gpt-4-turbo-preview",
                temperature=temperature,
            )

