"""
Sohay Search Module - Free web search implementation without API keys
"""

import os
import sys
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple, Union
from urllib.parse import quote_plus, urljoin

# List of user agents to rotate and avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
]

def get_random_user_agent():
    """Return a random user agent from the list"""
    return random.choice(USER_AGENTS)

def search_web(query: str, num_results: int = 10, max_retries: int = 3, retry_delay: int = 2) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo HTML search with improved reliability
    Returns a list of dictionaries with title, link, and snippet.
    
    Args:
        query: The search query string
        num_results: Maximum number of results to return
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries
        
    Returns:
        List of dictionaries with search results
    """
    # Format the query for URL
    search_term = quote_plus(query)
    
    # Try both DuckDuckGo HTML endpoints
    urls = [
        f"https://html.duckduckgo.com/html/?q={search_term}",
        f"https://duckduckgo.com/html/?q={search_term}"
    ]
    
    results = []
    attempts = 0
    
    while attempts < max_retries and not results:
        attempts += 1
        
        try:
            # Randomly select one of the URLs
            url = random.choice(urls)
            
            # Set up request with randomized headers to appear more like a browser
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "TE": "Trailers",
                "DNT": "1"  # Do Not Track
            }
            
            # Add a referer sometimes to make it more human-like
            if random.random() > 0.5:
                headers["Referer"] = "https://duckduckgo.com/"
            
            # Randomize the timeout slightly
            timeout = 10 + random.random() * 5
            
            # Make the request
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Parse the HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors for results to handle potential HTML structure changes
            # Method 1: Standard DuckDuckGo result container
            result_elements = soup.select('.result')
            
            # Method 2: Alternative structure sometimes used
            if not result_elements:
                result_elements = soup.select('.web-result')
            
            # Method 3: Even more generic approach
            if not result_elements:
                result_elements = soup.select('article')
            
            # Method 4: Try different result structure
            if not result_elements:
                result_elements = soup.select('.links_main')
            
            # Limit to requested number of results
            result_elements = result_elements[:num_results]
            
            for element in result_elements:
                # Try different selectors for title, URL, and snippet
                # Method 1: Standard structure
                title_element = element.select_one('.result__title')
                link_element = element.select_one('.result__url')
                snippet_element = element.select_one('.result__snippet')
                
                # Method 2: Alternative structure
                if not title_element:
                    title_element = element.select_one('h2')
                if not link_element:
                    link_element = element.select_one('a[href]')
                if not snippet_element:
                    snippet_element = element.select_one('.snippet')
                
                # Method 3: Even more generic
                if not title_element and link_element:
                    title_element = link_element
                if not snippet_element:
                    # Find any div with more than 15 characters as a fallback
                    for div in element.find_all('div'):
                        if div.text and len(div.text.strip()) > 15:
                            snippet_element = div
                            break
                
                # Extract data from elements
                title = title_element.get_text().strip() if title_element else "No title available"
                
                link = None
                if link_element:
                    if link_element.has_attr('href'):
                        link = link_element['href']
                    elif link_element.has_attr('data-href'):
                        link = link_element['data-href']
                
                # Sometimes DuckDuckGo uses relative URLs
                if link and not link.startswith(('http://', 'https://')):
                    if link.startswith('//'):
                        link = 'https:' + link
                    else:
                        link = urljoin('https://duckduckgo.com', link)
                
                # If still no link, use a generic Google search
                if not link:
                    link = f"https://www.google.com/search?q={search_term}"
                
                snippet = snippet_element.get_text().strip() if snippet_element else "No description available"
                
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
            
            # If we got results, we're done
            if results:
                break
            
            # If we didn't get results, wait a bit and try again
            time.sleep(retry_delay)
            
        except Exception as e:
            print(f"Search attempt {attempts} failed: {str(e)}")
            # Wait longer between retries
            time.sleep(retry_delay * attempts)
    
    # If no results after all retries, use fallback
    if not results:
        return fallback_search(query, num_results)
    
    return results

def fallback_search(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Fallback search method with improved results
    """
    try:
        # Try another search method - Bing
        search_term = quote_plus(query)
        url = f"https://www.bing.com/search?q={search_term}"
        
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse Bing search results
            results = []
            search_results = soup.select('.b_algo')
            
            for result in search_results[:num_results]:
                title_element = result.select_one('h2 a')
                link_element = result.select_one('h2 a')
                snippet_element = result.select_one('.b_caption p')
                
                if title_element and link_element:
                    title = title_element.get_text().strip()
                    link = link_element.get('href', '#')
                    snippet = snippet_element.get_text().strip() if snippet_element else "No description available"
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
            
            if results:
                return results
    except Exception as e:
        print(f"Bing fallback search failed: {str(e)}")
    
    # Last resort - return a basic result
    return [{
        "title": f"Search results for: {query}",
        "link": f"https://www.google.com/search?q={quote_plus(query)}",
        "snippet": "Direct Google search link. Please click to view results in your browser."
    }]

def format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into a readable string"""
    if not results:
        return "No search results found."
    
    formatted = "\n\n".join([
        f"Title: {result['title']}\nURL: {result['link']}\nDescription: {result['snippet']}"
        for result in results
    ])
    
    return formatted

def search_and_format(query: str, num_results: int = 10) -> str:
    """Search the web and return formatted results"""
    results = search_web(query, num_results)
    return format_search_results(results)

async def perform_search(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Asynchronous wrapper for search_web function.
    This is used by scripts that need async functionality.
    """
    # In a real async implementation, we would use aiohttp instead of requests
    # For now, we're just wrapping the synchronous function
    return search_web(query, num_results)

# Improved search to better handle specific topics like Bangladesh economy
def enhanced_search(query: str, topic_category: str = None, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Enhanced search that adds topic-specific keywords to improve search results
    """
    # If a topic category is provided, add relevant keywords
    if topic_category == "economy":
        # Add economic keywords to improve results
        enhanced_query = f"{query} economic data statistics analysis"
    elif topic_category == "finance":
        enhanced_query = f"{query} financial data analysis metrics"
    elif topic_category == "business":
        enhanced_query = f"{query} business market industry analysis"
    else:
        enhanced_query = query
        
    # Use the standard search with the enhanced query
    return search_web(enhanced_query, num_results)

# Async version of enhanced search
async def perform_enhanced_search(query: str, topic_category: str = None, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Asynchronous wrapper for enhanced_search function
    """
    return enhanced_search(query, topic_category, num_results)

if __name__ == "__main__":
    # Test the search functionality
    query = "Bangladesh economy GDP growth 2025"
    print(f"Searching for: {query}")
    results = search_web(query)
    print(format_search_results(results))
    
    # Test enhanced search
    print("\nTesting enhanced search:")
    enhanced_results = enhanced_search(query, "economy")
    print(format_search_results(enhanced_results)) 