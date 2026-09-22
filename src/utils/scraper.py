"""
Web scraping utility for competitor analysis.
Uses ddgs (formerly duckduckgo-search) to find text snippets containing competitor pricing.
"""
import time
from ddgs import DDGS
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_competitor_search_snippets(query: str, max_results: int = 3) -> str:
    """
    Searches the web for competitor products and returns concatenated text snippets.
    
    Args:
        query (str): The search query (e.g., "Benjara Black Chair price Wayfair").
        max_results (int): Number of results to fetch.
        
    Returns:
        str: Concatenated search snippets.
    """
    logger.info(f"Searching web for competitor pricing: '{query}'")
    snippets = []
    
    # 3-second cooldown to pace the requests
    time.sleep(3)
    
    try:
        with DDGS() as ddgs:
            # The new library uses a slightly different text() implementation
            results = ddgs.text(query, max_results=max_results)
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                snippets.append(f"Source: {title} | Snippet: {body}")
                
        if not snippets:
            logger.warning(f"No search results found for query: {query}")
            return "No competitor data found."
            
        return "\n---\n".join(snippets)
        
    except Exception as e:
        logger.error(f"Web search failed for query '{query}': {e}")
        return "Search failed. Default to derived reference price."