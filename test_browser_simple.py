"""
Simple test for browser integration using browser-use
"""

import os
import asyncio
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

async def main():
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in environment or .env file")
        return
    
    # Mask the API key for display
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"Using API key: {masked_key}")
    print("Testing browser automation with gpt-4o-mini model")
    
    try:
        # Simple task to test the browser
        task = "Go to https://www.wikipedia.org and search for 'Artificial Intelligence'"
        print(f"Task: {task}")
        
        # Create the agent directly - without headless parameter
        agent = Agent(
            task=task,
            llm=ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                openai_api_key=api_key,
            )
        )
        
        # Run the agent
        print("\nStarting browser automation...")
        await agent.run()
        
        print("\n✅ Browser automation test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during browser automation: {str(e)}")
        
        # Print detailed error information for troubleshooting
        import traceback
        print("\nError traceback:")
        traceback.print_exc()
        
        print("\nSuggestions:")
        print("1. Make sure browser-use is installed: pip install browser-use")
        print("2. Make sure Playwright is installed: python -m playwright install")
        print("3. Check if your OpenAI API key has access to gpt-4o-mini model")
        print("4. Try updating dependencies: pip install --upgrade browser-use playwright langchain langchain-openai")

if __name__ == "__main__":
    asyncio.run(main()) 