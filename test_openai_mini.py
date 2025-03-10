"""
Test script for OpenAI API with gpt-4o-mini model
"""

import os
import json
import requests
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in environment or .env file")
        return
    
    # Mask the API key for display
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"Using API key: {masked_key}")
    
    # Create request
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'This test of gpt-4o-mini was successful!' followed by a brief joke."}
        ],
        "temperature": 0.7
    }
    
    # Send request
    print(f"Sending request to {url}")
    print(f"Model: gpt-4o-mini")
    print("Waiting for response...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # Print status code
        print(f"Status code: {response.status_code}")
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            
            # Print model information
            print(f"Model used: {result.get('model', 'unknown')}")
            
            # Get the assistant's message
            message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"\nResponse:\n{message}")
            
            # Print token usage
            usage = result.get('usage', {})
            print(f"\nToken usage:")
            print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
            
            print("\n✅ API test successful!")
        else:
            print(f"\n❌ API test failed with status code: {response.status_code}")
            print(f"Error message: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Error making API request: {str(e)}")

if __name__ == "__main__":
    main() 