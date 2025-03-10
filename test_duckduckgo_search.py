#!/usr/bin/env python3
"""
Improved test script to verify the updated DuckDuckGo search implementation
"""

import os
import sys
import json
import time
import random
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

# Initialize colorama for colored output
colorama.init()

# Load environment variables
load_dotenv()

# Import search functionality
try:
    from sohay_search import search_web, enhanced_search, format_search_results
except ImportError:
    print(f"{Fore.RED}Error: Could not import sohay_search module.{Style.RESET_ALL}")
    print("Make sure sohay_search.py is in the current directory.")
    sys.exit(1)

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

def print_section(text):
    """Print a formatted section header"""
    print(f"\n{Fore.YELLOW}{text}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'-' * 60}{Style.RESET_ALL}")

def print_result(title, link, snippet, success=True):
    """Print a formatted search result"""
    color = Fore.GREEN if success else Fore.RED
    print(f"{color}Title:{Style.RESET_ALL} {title}")
    print(f"{color}URL:{Style.RESET_ALL} {link}")
    print(f"{color}Description:{Style.RESET_ALL} {snippet[:100]}{'...' if len(snippet) > 100 else ''}")
    print()

def test_search():
    """Test the improved search functionality with Bangladesh economy topics"""
    print_header("Testing Improved DuckDuckGo Search Implementation")
    
    # Test topics for Bangladesh economy
    topics = [
        "Bangladesh GDP growth rate 2025 projections",
        "Bangladesh inflation rate 2025 forecast",
        "Bangladesh garment industry exports 2025",
        "Bangladesh remittance inflows from Middle East 2025",
        "Bangladesh foreign exchange reserves 2025",
        "Bangladesh economic challenges 2025 climate change"
    ]
    
    # Track success rate
    total_searches = len(topics) * 2  # Regular + enhanced
    successful_searches = 0
    
    # Test regular search vs enhanced search
    for topic in topics:
        print_section(f"Testing search for: {topic}")
        
        # Regular search
        print(f"{Fore.MAGENTA}Regular search results:{Style.RESET_ALL}")
        try:
            regular_results = search_web(topic, num_results=3)
            if regular_results:
                # Count this as a success if we got at least one result
                successful_searches += 1
                
                # Print the results
                for result in regular_results:
                    print_result(result['title'], result['link'], result['snippet'])
            else:
                print(f"{Fore.RED}No search results found.{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{Fore.RED}Error in regular search: {str(e)}{Style.RESET_ALL}\n")
        
        # Enhanced search
        print(f"\n{Fore.MAGENTA}Enhanced search results:{Style.RESET_ALL}")
        try:
            enhanced_results = enhanced_search(topic, topic_category="economy", num_results=3)
            if enhanced_results:
                # Count this as a success if we got at least one result
                successful_searches += 1
                
                # Print the results
                for result in enhanced_results:
                    print_result(result['title'], result['link'], result['snippet'])
            else:
                print(f"{Fore.RED}No search results found.{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{Fore.RED}Error in enhanced search: {str(e)}{Style.RESET_ALL}\n")
        
        # Pause between topics to avoid rate limiting
        delay = 2 + random.random() * 3
        print(f"{Fore.BLUE}Waiting {delay:.1f} seconds before next query...{Style.RESET_ALL}")
        time.sleep(delay)
    
    # Print summary
    success_rate = (successful_searches / total_searches) * 100
    success_color = Fore.GREEN if success_rate >= 50 else (Fore.YELLOW if success_rate >= 25 else Fore.RED)
    
    print_header("Search Testing Completed")
    print(f"Total searches attempted: {total_searches}")
    print(f"Successful searches: {successful_searches}")
    print(f"Success rate: {success_color}{success_rate:.1f}%{Style.RESET_ALL}")
    
    if success_rate >= 50:
        print(f"\n{Fore.GREEN}✅ DuckDuckGo search is working reliably!{Style.RESET_ALL}")
    elif success_rate >= 25:
        print(f"\n{Fore.YELLOW}⚠️ DuckDuckGo search is working partially.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ DuckDuckGo search is still not working reliably.{Style.RESET_ALL}")

if __name__ == "__main__":
    test_search() 