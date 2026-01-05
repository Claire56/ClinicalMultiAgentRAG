"""Tavily service for real-time web search."""
from typing import List, Dict, Any, Optional
import asyncio
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.schema import Document
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class TavilyService:
    """Service for Tavily real-time web search."""
    
    def __init__(self):
        """Initialize Tavily service."""
        self.tavily_tool = None
        
        if not settings.TAVILY_API_KEY:
            logger.warning("Tavily API key not set. Real-time web search will be unavailable.")
            return
        
        if not settings.TAVILY_ENABLED:
            logger.info("Tavily is disabled in configuration")
            return
        
        try:
            self.tavily_tool = TavilySearchResults(
                tavily_api_key=settings.TAVILY_API_KEY,
                max_results=settings.TAVILY_MAX_RESULTS,
            )
            logger.info("Tavily service initialized", max_results=settings.TAVILY_MAX_RESULTS)
        except Exception as e:
            logger.error("Failed to initialize Tavily", error=str(e))
            self.tavily_tool = None
    
    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Search the web using Tavily.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            include_domains: List of domains to include (e.g., ["pubmed.ncbi.nlm.nih.gov"])
            exclude_domains: List of domains to exclude
        
        Returns:
            List of Document objects with search results
        """
        if not self.tavily_tool:
            logger.warning("Tavily tool not available")
            return []
        
        try:
            # Build search query with domain filters
            search_query = query
            
            # Add medical domain preferences
            if not include_domains:
                # Default to trusted medical sources
                include_domains = [
                    "pubmed.ncbi.nlm.nih.gov",
                    "nejm.org",
                    "bmj.com",
                    "jama.ama-assn.org",
                    "who.int",
                    "cdc.gov",
                    "nih.gov",
                ]
            
            # Execute search (TavilySearchResults uses sync invoke, but we'll wrap it)
            results = await asyncio.to_thread(
                self.tavily_tool.invoke,
                {
                    "query": search_query,
                    "search_depth": search_depth,
                    "include_domains": include_domains,
                    "exclude_domains": exclude_domains,
                }
            )
            
            # Convert to Document objects
            documents = []
            for result in results:
                doc = Document(
                    page_content=result.get("content", result.get("snippet", "")),
                    metadata={
                        "source": result.get("url", ""),
                        "title": result.get("title", ""),
                        "score": result.get("score", 0.0),
                        "published_date": result.get("published_date"),
                    }
                )
                documents.append(doc)
            
            logger.info(
                "Tavily search completed",
                query=query[:50],
                results_count=len(documents),
            )
            
            return documents
            
        except Exception as e:
            logger.error("Tavily search failed", error=str(e), query=query[:50])
            return []
    
    async def search_medical_literature(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> List[Document]:
        """
        Search for medical literature using trusted medical sources.
        
        Args:
            query: Medical research query
            max_results: Maximum number of results to return
        
        Returns:
            List of Document objects from medical sources
        """
        medical_domains = [
            "pubmed.ncbi.nlm.nih.gov",
            "nejm.org",
            "bmj.com",
            "jama.ama-assn.org",
            "thelancet.com",
            "nature.com",
            "science.org",
            "who.int",
            "cdc.gov",
            "nih.gov",
            "mayoclinic.org",
            "clevelandclinic.org",
        ]
        
        results = await self.search(
            query=query,
            search_depth="advanced",
            include_domains=medical_domains,
        )
        
        if max_results:
            results = results[:max_results]
        
        return results
    
    async def search_latest_guidelines(
        self,
        condition: str,
        max_results: Optional[int] = None,
    ) -> List[Document]:
        """
        Search for latest treatment guidelines for a condition.
        
        Args:
            condition: Medical condition (e.g., "diabetes", "hypertension")
            max_results: Maximum number of results
        
        Returns:
            List of Document objects with guideline information
        """
        query = f"latest treatment guidelines {condition} 2024"
        
        guideline_domains = [
            "who.int",
            "cdc.gov",
            "nih.gov",
            "acc.org",
            "heart.org",
            "diabetes.org",
            "acog.org",
        ]
        
        results = await self.search(
            query=query,
            search_depth="advanced",
            include_domains=guideline_domains,
        )
        
        if max_results:
            results = results[:max_results]
        
        return results

