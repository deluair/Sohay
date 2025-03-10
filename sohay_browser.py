"""
Sohay Browser Module - Browser automation capabilities for Sohay AI Assistant
Using browser-use (https://github.com/browser-use/browser-use)
"""

import os
import sys
import json
import asyncio
import requests
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import browser-use library - simplified to avoid import errors
try:
    # Direct imports
    from browser_use import Agent
    from langchain_openai import ChatOpenAI
    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = f"ImportError: {str(e)}"
    print(f"Browser-use import error: {IMPORT_ERROR}")
    print("Please install the required dependencies with:")
    print("pip install browser-use playwright langchain langchain-openai python-dotenv")
    print("python -m playwright install")
except Exception as e:
    IMPORT_ERROR = f"Error: {str(e)}"
    print(f"Browser-use error: {IMPORT_ERROR}")


class SohayBrowser:
    """Browser automation capabilities for Sohay using browser-use"""
    
    def __init__(self):
        """Initialize the browser module"""
        self.browser_initialized = False
        self.browser_agent = None
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.browser_headless = True  # Default to headless mode
        self.import_error = IMPORT_ERROR
        
        # Default browser settings
        self.browser_settings = {
            "headless": self.browser_headless,
            "slow_mo": 100,  # Slow down browser actions by 100ms
            "timeout": 30000,  # 30 seconds timeout
        }
    
    def test_openai_api(self) -> str:
        """Test if the OpenAI API key works by making a simple request"""
        if not self.openai_api_key:
            return "Error: OpenAI API key not set. Use set_openai_api_key method to set it."
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say this is a test!"}],
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return f"API test successful! Response: {message}"
            else:
                return f"API test failed with status code: {response.status_code}. Response: {response.text}"
        except Exception as e:
            return f"Error testing OpenAI API: {str(e)}"
    
    async def initialize_browser(self, headless: bool = True, debug: bool = False) -> str:
        """Initialize the browser with the specified settings"""
        # Check for import errors
        if self.import_error:
            return f"Error: Browser-use module not properly imported. {self.import_error}"
        
        if not self.openai_api_key:
            return "Error: OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
        
        # Test the API key first
        api_test_result = self.test_openai_api()
        if "API test failed" in api_test_result or "Error testing" in api_test_result:
            return f"Error initializing browser: {api_test_result}"
        
        try:
            # Update headless mode setting (stored but not used directly)
            self.browser_headless = headless
            
            # Print info about initialization
            print(f"Initializing browser with settings:")
            print(f"- Headless mode: {headless} (Note: browser-use controls this setting)")
            print(f"- Debug mode: {debug}")
            print(f"Using OpenAI API key: {self.openai_api_key[:8]}...{self.openai_api_key[-4:]}")
            
            # Don't create the agent until needed - just mark as initialized
            self.browser_initialized = True
            
            return "Browser initialized successfully. Ready for web automation tasks."
        
        except Exception as e:
            return f"Error initializing browser: {str(e)}"
    
    async def browse(self, instruction: str) -> str:
        """Execute a browsing task with the provided instruction"""
        if self.import_error:
            return f"Error: Browser-use module not properly imported. {self.import_error}"
            
        if not self.browser_initialized:
            init_result = await self.initialize_browser()
            if "Error" in init_result:
                return init_result
        
        try:
            print(f"Executing browser task: {instruction}")
            
            # Create the agent for this specific task - without headless
            agent = Agent(
                task=instruction,
                llm=ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0,
                    openai_api_key=self.openai_api_key,
                )
            )
            
            # Run the agent
            print("Running browser agent...")
            await agent.run()
            
            # Get the result
            result = "Browser task completed successfully."
            return result
            
        except Exception as e:
            return f"Error executing browser task: {str(e)}"
    
    async def browse_url(self, url: str, task: Optional[str] = None) -> str:
        """Browse to a specific URL and optionally perform a task"""
        instruction = f"Go to {url}"
        if task:
            instruction += f" and {task}"
        
        return await self.browse(instruction)
    
    async def close_browser(self) -> str:
        """Close the browser and clean up resources"""
        if not self.browser_initialized:
            return "Browser is not initialized."
        
        try:
            # No explicit cleanup needed for Agent-based approach
            self.browser_initialized = False
            return "Browser closed successfully."
        except Exception as e:
            return f"Error closing browser: {str(e)}"
    
    async def take_screenshot(self, filename: str = "screenshot.png") -> str:
        """Take a screenshot of the current browser page"""
        if not self.browser_initialized:
            init_result = await self.initialize_browser()
            if "Error" in init_result:
                return init_result
        
        try:
            # Create a specific task for screenshot
            instruction = f"Take a screenshot and save it as {filename}"
            
            # Execute the task
            return await self.browse(instruction)
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    def set_openai_api_key(self, api_key: str) -> str:
        """Set the OpenAI API key for browser agent"""
        if not api_key:
            return "Error: API key cannot be empty"
        
        self.openai_api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Reset browser to use new API key
        if self.browser_initialized:
            self.browser_initialized = False
        
        return "OpenAI API key set successfully."
    
    async def run_command(self, command: str, args: Dict[str, Any] = None) -> str:
        """Run a browser command with arguments"""
        if args is None:
            args = {}
        
        # Handle different browser commands
        if command.lower() == "open":
            url = args.get("url", "")
            if not url:
                return "Error: URL is required for 'open' command"
            
            headless = not args.get("visible", False)  # Default to headless unless visible=True
            
            if not self.browser_initialized or self.browser_headless != headless:
                await self.initialize_browser(headless=headless)
            
            return await self.browse_url(url)
        
        elif command.lower() == "search":
            query = args.get("query", "")
            if not query:
                return "Error: Query is required for 'search' command"
            
            # Build a task for web search
            task = f"Search for '{query}' on Google and extract the top results"
            return await self.browse(task)
        
        elif command.lower() == "screenshot":
            filename = args.get("filename", "screenshot.png")
            return await self.take_screenshot(filename)
        
        elif command.lower() == "close":
            return await self.close_browser()
        
        else:
            return f"Unknown browser command: {command}"


# Example usage
async def main():
    """Example usage of SohayBrowser"""
    browser = SohayBrowser()
    result = await browser.initialize_browser(headless=False)
    print(result)
    
    result = await browser.browse("Go to https://www.wikipedia.org and search for 'Artificial Intelligence'")
    print(result)
    
    await browser.close_browser()

if __name__ == "__main__":
    asyncio.run(main()) 