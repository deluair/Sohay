"""
Sohay Search Module - Free web search implementation without API keys
"""

import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple, Union
from urllib.parse import quote_plus

def search_web(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Search the web using a free alternative to Google Search API
    Returns a list of dictionaries with title, link, and snippet.
    """
    try:
        # Format the query for URL
        search_term = quote_plus(query)
        
        # Use DuckDuckGo HTML search (doesn't require API key)
        url = f"https://html.duckduckgo.com/html/?q={search_term}"
        
        # Set up request with headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results
        results = []
        result_elements = soup.select('.result')[:num_results]
        
        for element in result_elements:
            title_element = element.select_one('.result__title')
            link_element = element.select_one('.result__url')
            snippet_element = element.select_one('.result__snippet')
            
            title = title_element.get_text().strip() if title_element else "No title available"
            link = link_element.get('href') if link_element else "#"
            snippet = snippet_element.get_text().strip() if snippet_element else "No description available"
            
            results.append({
                "title": title,
                "link": link,
                "snippet": snippet
            })
        
        return results
        
    except Exception as e:
        # Fallback to a simpler method if DuckDuckGo fails
        try:
            return fallback_search(query, num_results)
        except Exception as inner_e:
            print(f"Error in fallback search: {str(inner_e)}")
            # Return a minimal result with the error
            return [{
                "title": "Search Error",
                "link": f"https://www.google.com/search?q={quote_plus(query)}",
                "snippet": f"Search failed: {str(e)}. Please try manually searching the query."
            }]

def fallback_search(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Fallback search method that doesn't require HTML parsing
    """
    # Create a search URL for Google
    google_url = f"https://www.google.com/search?q={quote_plus(query)}"
    
    # Return a basic result with the Google URL
    return [{
        "title": f"Search results for: {query}",
        "link": google_url,
        "snippet": "Direct Google search link. Please click to view results in your browser."
    }]

def format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into a readable text string"""
    if not results:
        return "No search results found."
    
    formatted = f"Search results ({len(results)} items):\n\n"
    
    for i, result in enumerate(results):
        formatted += f"{i+1}. {result['title']}\n"
        formatted += f"   {result['link']}\n"
        formatted += f"   {result['snippet']}\n\n"
    
    return formatted

def search_and_format(query: str, num_results: int = 10) -> str:
    """Search the web and return formatted results"""
    results = search_web(query, num_results)
    return format_search_results(results)

# Example usage
if __name__ == "__main__":
    query = "quantum computing recent advancements"
    results = search_web(query)
    formatted = format_search_results(results)
    print(formatted) 