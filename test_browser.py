"""
Test script for Sohay Browser Module
"""

import os
import json
import asyncio
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_api(api_key):
    """Test if the OpenAI API key works by making a simple request"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "temperature": 0.7
    }
    
    print(f"Testing OpenAI API key with a simple request to {data['model']}...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"API test successful! Response: {message}")
            return True
        else:
            print(f"API test failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing OpenAI API: {str(e)}")
        return False

# Check if OpenAI API key is set
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not set. Please set it in your environment or .env file.")
    print("You can get an API key from https://platform.openai.com/api-keys")
    api_key = input("Enter your OpenAI API key (or press Enter to quit): ")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        openai_api_key = api_key
    else:
        print("No API key provided. Exiting.")
        exit(1)
else:
    # Test if the API key works
    if not test_openai_api(openai_api_key):
        print("OpenAI API key test failed. You may still proceed, but browser functionality might not work.")
        proceed = input("Do you want to continue anyway? (y/n): ").lower()
        if proceed != 'y':
            exit(1)

try:
    from sohay_browser import SohayBrowser
except ImportError:
    print("Error: sohay_browser module not found.")
    print("Make sure you have installed all dependencies:")
    print("pip install browser-use playwright langchain langchain-openai python-dotenv")
    print("python -m playwright install")
    exit(1)

async def main():
    parser = argparse.ArgumentParser(description="Test Sohay Browser Module")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--url", default="https://www.wikipedia.org", help="URL to browse")
    parser.add_argument("--task", default="search for 'artificial intelligence'", help="Task to perform")
    parser.add_argument("--test-api-only", action="store_true", help="Only test the OpenAI API and exit")
    args = parser.parse_args()
    
    # If testing API only, exit after API test
    if args.test_api_only:
        print("API test completed. Exiting.")
        return
    
    # Print settings
    print(f"Testing browser with the following settings:")
    print(f"- Headless mode: {args.headless}")
    print(f"- URL: {args.url}")
    print(f"- Task: {args.task}")
    print(f"- API key: {openai_api_key[:4]}...{openai_api_key[-4:]}")
    
    # Initialize browser
    browser = SohayBrowser()
    result = await browser.initialize_browser(headless=args.headless, debug=True)
    print(f"Initialization result: {result}")
    
    if "Error" in result:
        print("Failed to initialize browser. Exiting.")
        return
    
    try:
        # Browse to URL and perform task
        instruction = f"Go to {args.url} and {args.task}"
        print(f"\nExecuting instruction: {instruction}")
        result = await browser.browse(instruction)
        print(f"\nResult:\n{result}")
    finally:
        # Close browser
        print("\nClosing browser...")
        await browser.close_browser()

if __name__ == "__main__":
    asyncio.run(main()) 