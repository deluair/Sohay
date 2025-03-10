import json
import os
import sys
import argparse
import re
import requests
import subprocess
import platform
import shlex
import time
import textwrap
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import threading

# Try to import the browser module
BROWSER_AVAILABLE = False
BROWSER_ERROR = None
try:
    # First try simple browser-use import to check if module exists
    import browser_use
    
    # Import types we need from langchain
    import langchain_openai
    
    # Now try to import our wrapper module
    from sohay_browser import SohayBrowser, IMPORT_ERROR
    
    # Only mark as available if there was no import error in the module
    if IMPORT_ERROR is None:
        BROWSER_AVAILABLE = True
    else:
        BROWSER_ERROR = IMPORT_ERROR
        print(f"Browser module imported but has errors: {BROWSER_ERROR}")
except ImportError as e:
    BROWSER_ERROR = str(e)
    BROWSER_AVAILABLE = False
    print(f"Browser automation not available: {BROWSER_ERROR}")
    print("To enable browser automation, install the required dependencies:")
    print("pip install browser-use playwright langchain langchain-openai python-dotenv")
    print("python -m playwright install")
except Exception as e:
    BROWSER_ERROR = str(e)
    BROWSER_AVAILABLE = False
    print(f"Error initializing browser module: {BROWSER_ERROR}")

# Try to import the agent module
try:
    from sohay_agent import SohayAgent
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    print(f"Autonomous agent capabilities not available: {str(e)}")

# Import our new search module
try:
    from sohay_search import search_and_format
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    print("Free search functionality not available. Creating search module...")

class TextColors:
    """Text colors for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def disable_if_needed():
        """Disable colors if not supported"""
        if platform.system() == 'Windows':
            # Enable VT100 emulation on Windows
            os.system('')
        
        # Check if colors are supported
        if not sys.stdout.isatty():
            TextColors.HEADER = ''
            TextColors.BLUE = ''
            TextColors.GREEN = ''
            TextColors.YELLOW = ''
            TextColors.RED = ''
            TextColors.ENDC = ''
            TextColors.BOLD = ''
            TextColors.UNDERLINE = ''

class SohayAssistant:
    """
    Implementation of Sohay AI Assistant that can run tasks based on the
    capabilities defined in sohay.json
    """
    
    def __init__(self, config_path: str = "sohay.json"):
        """Initialize the Sohay assistant with configuration"""
        # Setup text colors
        TextColors.disable_if_needed()
        
        self.config_path = config_path
        self.tools = {}
        self.active_shells = {}
        self.current_shell_id = "default"
        self.working_language = "English"
        self.last_command_time = time.time()
        
        # Google Search API configuration
        # Use the provided API key and a public custom search engine ID
        self.google_api_key = os.environ.get('GOOGLE_API_KEY', 'AIzaSyAwqs8DlJVh7fceNw8Mr4d_NVO9AvfRdz4')
        
        # Using a common public CSE ID for web search - this is the fallback
        # Users should replace this with their own for production use
        self.google_cse_id = os.environ.get('GOOGLE_CSE_ID', '009789494739016300682:xvqdritwg5g')
        
        # Command history for up/down arrow support
        self.command_history = []
        self.command_index = 0
        
        # Initialize browser if available
        self.browser = None
        if BROWSER_AVAILABLE:
            self.browser = SohayBrowser()
            print(f"{TextColors.BLUE}Browser automation capabilities available{TextColors.ENDC}")
        
        # Initialize autonomous agent if available
        self.agent = None
        self.agent_thread = None
        self.agent_running = False
        if AGENT_AVAILABLE:
            self.agent = SohayAgent(self)
            print(f"{TextColors.BLUE}Autonomous agent capabilities available{TextColors.ENDC}")
        
        self.load_config()
        
        # Set up default shell
        self.active_shells[self.current_shell_id] = {
            "cwd": os.getcwd(),
            "history": []
        }
        
    def load_config(self) -> None:
        """Load tools and capabilities from the config file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Extract all function definitions
            for item in config:
                if item.get("type") == "function" and "function" in item:
                    func_def = item["function"]
                    self.tools[func_def["name"]] = func_def
            
            print(f"{TextColors.GREEN}Successfully loaded {len(self.tools)} tools from configuration{TextColors.ENDC}")
        except FileNotFoundError:
            print(f"{TextColors.RED}Error: Configuration file '{self.config_path}' not found{TextColors.ENDC}")
            print(f"Please make sure the file exists in the current directory or provide the correct path.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"{TextColors.RED}Error: Invalid JSON in configuration file{TextColors.ENDC}")
            print(f"Please check the format of '{self.config_path}'.")
            sys.exit(1)
        except Exception as e:
            print(f"{TextColors.RED}Error loading configuration: {str(e)}{TextColors.ENDC}")
            sys.exit(1)
    
    def list_capabilities(self) -> None:
        """Display the available capabilities/tools"""
        print(f"\n{TextColors.HEADER}Sohay Assistant Capabilities:{TextColors.ENDC}")
        print("============================")
        
        # Group tools by category
        categories = {}
        for name, tool in self.tools.items():
            # Extract category from description if possible
            desc = tool.get('description', '')
            if '. Use ' in desc:
                category = desc.split('. Use ')[1].split('.')[0].strip()
            else:
                category = "Other"
                
            if category not in categories:
                categories[category] = []
            categories[category].append((name, desc))
        
        # Print tools by category
        for category, tools in sorted(categories.items()):
            print(f"\n{TextColors.BOLD}{category}:{TextColors.ENDC}")
            for name, desc in sorted(tools):
                short_desc = desc.split('.')[0] if '.' in desc else desc
                print(f"  - {TextColors.BLUE}{name}{TextColors.ENDC}: {short_desc}")
        
        # Show browser capabilities if available
        if BROWSER_AVAILABLE:
            print(f"\n{TextColors.BOLD}Browser Automation:{TextColors.ENDC}")
            print(f"  - {TextColors.BLUE}browse [url]{TextColors.ENDC}: Open a website and interact with it")
            print(f"  - {TextColors.BLUE}websearch [query]{TextColors.ENDC}: Search the web and extract results")
            print(f"  - {TextColors.BLUE}screenshot [filename]{TextColors.ENDC}: Take a screenshot of the current page")
    
    def google_search(self, query: str, date_range: str = "all") -> str:
        """Perform a web search using free search implementation"""
        # Always attempt to use the free search implementation first
        try:
            if SEARCH_AVAILABLE:
                print(f"{TextColors.YELLOW}Searching for: {query}{TextColors.ENDC}")
                
                if date_range != "all":
                    # Add time constraint to the query
                    time_words = {
                        "past_hour": "past hour",
                        "past_day": "past 24 hours", 
                        "past_week": "past week",
                        "past_month": "past month",
                        "past_year": "past year"
                    }
                    time_phrase = time_words.get(date_range, "")
                    if time_phrase:
                        query = f"{query} {time_phrase}"
                    print(f"{TextColors.YELLOW}With date filter: {time_phrase}{TextColors.ENDC}")
                
                # Call our free search implementation
                search_results = search_and_format(query)
                return f"{TextColors.GREEN}Search results for '{query}':{TextColors.ENDC}\n\n{search_results}"
            else:
                return self.fallback_search(query)
        except Exception as e:
            error_message = f"Search error: {str(e)}"
            print(f"{TextColors.RED}{error_message}{TextColors.ENDC}")
            return self.fallback_search(query)
    
    def fallback_search(self, query: str) -> str:
        """Fallback search method when API fails"""
        try:
            # Format the query for a Google search URL
            formatted_query = query.replace(' ', '+')
            search_url = f"https://www.google.com/search?q={formatted_query}"
            
            result = (f"{TextColors.YELLOW}I attempted to search for '{query}' but encountered an issue with the Google API.{TextColors.ENDC}\n\n"
                     f"You can view the results by visiting this URL:\n{TextColors.BLUE}{search_url}{TextColors.ENDC}\n\n"
                     f"Alternative option: Use a different API key or CSE ID by typing 'setup google'")
            
            return result
        except Exception as e:
            return f"{TextColors.RED}Unable to perform search: {str(e)}{TextColors.ENDC}"
    
    def read_file(self, file_path: str, max_lines: int = 1000) -> str:
        """Read and display file contents with syntax highlighting"""
        try:
            # Validate the file path
            if not os.path.exists(file_path):
                return f"{TextColors.RED}Error: File '{file_path}' not found{TextColors.ENDC}"
            
            if not os.path.isfile(file_path):
                return f"{TextColors.RED}Error: '{file_path}' is not a file{TextColors.ENDC}"
            
            # Get file extension for syntax highlighting (future enhancement)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Get file size
            file_size = os.path.getsize(file_path)
            file_size_str = self.format_file_size(file_size)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Truncate if too many lines
            total_lines = len(lines)
            if total_lines > max_lines:
                displayed_lines = lines[:max_lines]
                truncated_msg = f"\n{TextColors.YELLOW}... (truncated {total_lines - max_lines} of {total_lines} lines) ...{TextColors.ENDC}\n"
            else:
                displayed_lines = lines
                truncated_msg = ""
            
            # Format content
            content = ''.join(displayed_lines)
            
            # Add file information header
            result = f"{TextColors.BOLD}File: {file_path}{TextColors.ENDC}\n"
            result += f"Size: {file_size_str}, Lines: {total_lines}\n"
            result += f"{'-' * 50}\n\n"
            result += content
            
            if truncated_msg:
                result += truncated_msg
            
            return result
            
        except UnicodeDecodeError:
            return f"{TextColors.RED}Error: Cannot read '{file_path}' - file appears to be binary{TextColors.ENDC}"
        except Exception as e:
            return f"{TextColors.RED}Error reading file: {str(e)}{TextColors.ENDC}"

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size from bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def execute_shell_command(self, command: str, shell_id: str, cwd: str) -> str:
        """Execute a shell command and return the result"""
        is_windows = platform.system() == "Windows"
        
        try:
            if is_windows:
                # On Windows, use subprocess with shell=True
                process = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    cwd=cwd,
                    timeout=15
                )
            else:
                # On Unix, use shlex.split and shell=False for better security
                process = subprocess.run(
                    shlex.split(command),
                    shell=False,
                    text=True,
                    capture_output=True,
                    cwd=cwd,
                    timeout=15
                )
            
            output = process.stdout
            error = process.stderr
            
            # Format the result
            result = f"{TextColors.BOLD}$ {command}{TextColors.ENDC}\n"
            
            # Handle successful execution
            if process.returncode == 0:
                if output:
                    result += output
                else:
                    result += "(Command executed successfully with no output)\n"
            else:
                # Handle error
                result += f"{TextColors.RED}Command failed with exit code {process.returncode}{TextColors.ENDC}\n"
                if error:
                    result += f"{TextColors.RED}{error}{TextColors.ENDC}"
            
            return result
            
        except subprocess.TimeoutExpired:
            return f"{TextColors.RED}Command timed out after 15 seconds{TextColors.ENDC}"
        except Exception as e:
            return f"{TextColors.RED}Error executing command: {str(e)}{TextColors.ENDC}"
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool with the given parameters"""
        if tool_name not in self.tools:
            return f"{TextColors.RED}Error: Tool '{tool_name}' not found{TextColors.ENDC}"
        
        # Record the time of the last command
        self.last_command_time = time.time()
        
        # Simple mock implementations for demo purposes
        if tool_name == "message_notify_user":
            return f"{TextColors.GREEN}NOTIFICATION: {params.get('text', '')}{TextColors.ENDC}"
        
        elif tool_name == "message_ask_user":
            user_input = input(f"{TextColors.YELLOW}QUESTION: {params.get('text', '')}{TextColors.ENDC}\nYour answer: ")
            return f"{TextColors.GREEN}User responded: {user_input}{TextColors.ENDC}"
        
        elif tool_name == "file_read":
            file_path = params.get('file', '')
            return self.read_file(file_path)
        
        elif tool_name == "shell_exec":
            shell_id = params.get('id', self.current_shell_id)
            command = params.get('command', '')
            
            if shell_id not in self.active_shells:
                self.active_shells[shell_id] = {
                    "cwd": params.get('exec_dir', os.getcwd()),
                    "history": []
                }
                
            self.active_shells[shell_id]["history"].append(command)
            
            # For commands, actually execute them if safe
            safe_commands = ['ls', 'dir', 'echo', 'type', 'cat', 'pwd', 'date', 'time', 'whoami', 
                            'cd', 'mkdir', 'rmdir', 'touch', 'cp', 'copy', 'mv', 'move', 'find',
                            'grep', 'python', 'pip', 'npm', 'node']
            is_safe = any(command.split()[0].lower() == cmd for cmd in safe_commands)
            
            if is_safe:
                cwd = self.active_shells[shell_id]["cwd"]
                return self.execute_shell_command(command, shell_id, cwd)
            else:
                return f"{TextColors.YELLOW}Command '{command}' not executed for safety reasons.{TextColors.ENDC}\n" \
                       f"Only basic file and directory commands are allowed in this demo."
        
        elif tool_name == "info_search_web":
            query = params.get('query', '')
            date_range = params.get('date_range', 'all')
            return self.google_search(query, date_range)
        
        elif tool_name == "idle":
            return f"{TextColors.BLUE}Assistant entering idle state.{TextColors.ENDC}"
            
        return f"{TextColors.YELLOW}Tool {tool_name} called with params: {params}{TextColors.ENDC}\n" \
               f"(This is a simulation, tool not fully implemented)"
    
    def configure_google_api(self) -> None:
        """Configure Google API credentials interactively"""
        print(f"\n{TextColors.HEADER}Google Search API Configuration{TextColors.ENDC}")
        print("===============================")
        
        print(f"\n{TextColors.BOLD}Current API settings:{TextColors.ENDC}")
        print(f"API Key: {self.google_api_key[:4]}...{self.google_api_key[-4:] if len(self.google_api_key) > 8 else ''}")
        print(f"CSE ID: {self.google_cse_id}")
        
        print(f"\n{TextColors.BOLD}Enter new credentials (or press Enter to keep current values):{TextColors.ENDC}")
        
        api_key = input("Enter your Google API Key: ").strip()
        if api_key:
            self.google_api_key = api_key
            os.environ['GOOGLE_API_KEY'] = api_key
        
        cse_id = input("Enter your Custom Search Engine ID: ").strip()
        if cse_id:
            self.google_cse_id = cse_id
            os.environ['GOOGLE_CSE_ID'] = cse_id
        
        print(f"\n{TextColors.GREEN}API credentials updated for this session.{TextColors.ENDC}")
        print("To make them permanent, add these to your environment variables:")
        print(f"GOOGLE_API_KEY={self.google_api_key}")
        print(f"GOOGLE_CSE_ID={self.google_cse_id}")
        
        # Test the search with current settings
        print(f"\n{TextColors.YELLOW}Testing search with current settings...{TextColors.ENDC}")
        test_result = self.google_search("test query", "all")
        if "error" in test_result.lower() or "unable" in test_result.lower():
            print(f"{TextColors.RED}Warning: Search test encountered issues. You may need to check your credentials.{TextColors.ENDC}")
        else:
            print(f"{TextColors.GREEN}Search test successful!{TextColors.ENDC}")
    
    def configure_openai_api(self) -> None:
        """Configure OpenAI API key for browser automation"""
        if not BROWSER_AVAILABLE:
            print(f"{TextColors.RED}Browser automation module not available{TextColors.ENDC}")
            print("Please install the required dependencies with:")
            print("pip install browser-use playwright langchain langchain-openai python-dotenv")
            return
        
        print(f"\n{TextColors.HEADER}OpenAI API Configuration{TextColors.ENDC}")
        print("=============================")
        
        current_key = os.environ.get("OPENAI_API_KEY", "")
        if current_key:
            masked_key = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 8 else ""
            print(f"Current API key: {masked_key}")
        else:
            print("No API key currently set")
        
        api_key = input("\nEnter your OpenAI API key: ").strip()
        
        if api_key:
            result = self.browser.set_openai_api_key(api_key)
            print(f"\n{TextColors.GREEN}{result}{TextColors.ENDC}")
            print("API key will be used for browser automation tasks")
            print(f"\nWould you like to test the API key now? (y/n): ")
            if input().lower() == 'y':
                self.test_openai_api()
        else:
            print(f"\n{TextColors.YELLOW}API key not updated{TextColors.ENDC}")
            
    def test_openai_api(self) -> None:
        """Test the OpenAI API key"""
        if not BROWSER_AVAILABLE:
            print(f"{TextColors.RED}Browser automation module not available{TextColors.ENDC}")
            print("Please install the required dependencies with:")
            print("pip install browser-use playwright langchain langchain-openai python-dotenv")
            return
            
        if not self.browser:
            self.browser = SohayBrowser()
            
        print(f"\n{TextColors.HEADER}OpenAI API Test{TextColors.ENDC}")
        print("=================")
        
        result = self.browser.test_openai_api()
        
        if "API test successful" in result:
            print(f"\n{TextColors.GREEN}{result}{TextColors.ENDC}")
            print("\nYour API key is working correctly and can be used for browser automation.")
        else:
            print(f"\n{TextColors.RED}{result}{TextColors.ENDC}")
            print("\nYour API key is not working. Please check it and try again.")
            print("You can set a new API key with the 'setup openai' command.")
        
        print("\nFor more testing options, use:")
        print(" - ./test_openai_api.sh (Linux/Mac)")
        print(" - .\\test_openai_api.ps1 (Windows)")
        print(" - python test_browser.py --test-api-only")
    
    async def execute_browser_command(self, command: str, args: Dict[str, Any]) -> str:
        """Execute a browser command using browser-use"""
        if not BROWSER_AVAILABLE:
            return f"{TextColors.RED}Browser automation module not available.{TextColors.ENDC}\nPlease install required dependencies with:\npip install browser-use playwright langchain langchain-openai python-dotenv"
        
        try:
            # Initialize browser if needed
            if not self.browser:
                self.browser = SohayBrowser()
            
            # Run the command
            return await self.browser.run_command(command, args)
        except Exception as e:
            return f"{TextColors.RED}Error executing browser command: {str(e)}{TextColors.ENDC}"
    
    def parse_tool_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Parse the user input to identify potential tool calls"""
        # Add to command history if not empty
        if user_input.strip():
            self.command_history.append(user_input)
            self.command_index = len(self.command_history)
        
        # Pattern matching for browser commands
        browser_patterns = {
            "browse": [
                r"(?i)^browse\s+(?:to\s+)?(?:the\s+)?(?:website\s+)?(?:url\s+)?(.+)",
                r"(?i)^open\s+(?:website|url|page|site)\s+(.+)",
                r"(?i)^go\s+to\s+(?:website|url|page|site)\s+(.+)"
            ],
            "websearch": [
                r"(?i)^websearch\s+(?:for\s+)?(.+)",
                r"(?i)^web\s+search\s+(?:for\s+)?(.+)",
                r"(?i)^browser\s+search\s+(?:for\s+)?(.+)"
            ],
            "screenshot": [
                r"(?i)^screenshot\s+(?:as\s+)?(?:filename\s+)?(.+)?",
                r"(?i)^take\s+(?:a\s+)?screenshot\s+(?:as\s+)?(?:filename\s+)?(.+)?"
            ]
        }
        
        # Check browser patterns if browser is available
        if BROWSER_AVAILABLE:
            for command, patterns in browser_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, user_input)
                    if match:
                        content = match.group(1).strip() if match.group(1) else ""
                        
                        if command == "browse":
                            # Extract URL from match
                            url = content
                            # Check if URL starts with http:// or https://
                            if not url.startswith(("http://", "https://")):
                                url = "https://" + url
                            
                            return {
                                "browser": "open",
                                "args": {"url": url, "visible": True}
                            }
                        
                        elif command == "websearch":
                            return {
                                "browser": "search",
                                "args": {"query": content}
                            }
                        
                        elif command == "screenshot":
                            filename = content if content else "screenshot.png"
                            return {
                                "browser": "screenshot",
                                "args": {"filename": filename}
                            }
        
        # Simple pattern matching for demo purposes
        tool_patterns = {
            "search": [
                r"(?i)^search\s+(?:for\s+)?(.+)",
                r"(?i)^find\s+(?:information\s+(?:about|on)\s+)?(.+)",
                r"(?i)^look\s+(?:up|for)\s+(.+)"
            ],
            "read": [
                r"(?i)^read\s+(?:file\s+)?(.+)",
                r"(?i)^open\s+(?:file\s+)?(.+)",
                r"(?i)^show\s+(?:file\s+)?(.+)",
                r"(?i)^cat\s+(.+)",
                r"(?i)^type\s+(.+)"
            ],
            "execute": [
                r"(?i)^(?:run|execute)\s+(?:command\s+)?(.+)",
                r"(?i)^(?:shell|cmd|command)\s+(.+)",
                r"(?i)^(?:bash|sh|powershell)\s+(.+)",
                r"(?i)^>\s*(.+)"
            ],
            "message": [
                r"(?i)^(?:send|notify)\s+(?:message\s+)?(.+)",
                r"(?i)^(?:alert|inform)\s+(?:user\s+with\s+)?(.+)",
                r"(?i)^(?:tell|say)\s+(.+)"
            ]
        }
        
        for tool_type, patterns in tool_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_input)
                if match:
                    content = match.group(1).strip()
                    
                    if tool_type == "search":
                        # Extract date range if specified (e.g. "search for AI news from past week")
                        date_pattern = r"(?i)from\s+(past\s+(?:hour|day|week|month|year))"
                        date_match = re.search(date_pattern, content)
                        date_range = "all"
                        
                        if date_match:
                            date_text = date_match.group(1).lower()
                            # Convert "past hour/day/week/month/year" to expected format
                            date_map = {
                                "past hour": "past_hour",
                                "past day": "past_day",
                                "past week": "past_week",
                                "past month": "past_month",
                                "past year": "past_year"
                            }
                            date_range = date_map.get(date_text, "all")
                            # Remove date part from query
                            content = re.sub(date_pattern, "", content).strip()
                        
                        return {
                            "tool": "info_search_web",
                            "params": {"query": content, "date_range": date_range}
                        }
                    elif tool_type == "read":
                        # Handle shortcuts like '.' or '..' for current/parent directory
                        if content == '.':
                            content = os.getcwd()
                        elif content == '..':
                            content = os.path.dirname(os.getcwd())
                        
                        return {
                            "tool": "file_read",
                            "params": {"file": content}
                        }
                    elif tool_type == "execute":
                        # Handle special case for 'cd' command to change directory
                        if content.startswith('cd '):
                            try:
                                # Get the directory path
                                dir_path = content[3:].strip()
                                
                                # Handle relative paths
                                if not os.path.isabs(dir_path):
                                    current_dir = self.active_shells[self.current_shell_id]["cwd"]
                                    dir_path = os.path.join(current_dir, dir_path)
                                
                                # Normalize path
                                dir_path = os.path.normpath(dir_path)
                                
                                # Check if directory exists
                                if os.path.isdir(dir_path):
                                    self.active_shells[self.current_shell_id]["cwd"] = dir_path
                                    return {
                                        "tool": "shell_exec",
                                        "params": {
                                            "id": self.current_shell_id,
                                            "exec_dir": dir_path,
                                            "command": content
                                        }
                                    }
                                else:
                                    return {
                                        "error": f"Directory not found: {dir_path}"
                                    }
                            except Exception as e:
                                return {
                                    "error": f"Error changing directory: {str(e)}"
                                }
                        
                        return {
                            "tool": "shell_exec",
                            "params": {
                                "id": self.current_shell_id,
                                "exec_dir": self.active_shells[self.current_shell_id]["cwd"],
                                "command": content
                            }
                        }
                    elif tool_type == "message":
                        return {
                            "tool": "message_notify_user",
                            "params": {"text": content}
                        }
        
        # Handle system commands
        if user_input.lower() in ["help", "capabilities", "commands", "?", "/?", "--help"]:
            return {"system": "help"}
        elif user_input.lower() in ["setup google", "configure google", "setup search"]:
            return {"system": "setup_google"}
        elif user_input.lower() in ["setup openai", "configure openai", "openai key", "set api key"]:
            return {"system": "setup_openai"}
        elif user_input.lower() in ["test openai", "test api", "verify api", "check api"]:
            return {"system": "test_openai"}
        elif user_input.lower() in ["test browser", "browser test", "check browser"]:
            return {"system": "test_browser"}
        elif user_input.lower() in ["exit", "quit", "bye", "q", "exit()"]:
            return {"system": "exit"}
        elif user_input.lower() == "clear" or user_input.lower() == "cls":
            # Clear the screen
            os.system('cls' if platform.system() == 'Windows' else 'clear')
            return {"system": "clear"}
        elif user_input.lower() in ["status", "info", "sohay status"]:
            return {"system": "status"}
        elif user_input.lower() in ["current directory", "pwd", "where am i"]:
            return {"system": "current_directory"}
        
        return None
    
    def show_status(self) -> None:
        """Show the current status of the assistant"""
        print(f"\n{TextColors.HEADER}Sohay Assistant Status{TextColors.ENDC}")
        print("=======================")
        
        # System information
        print(f"\n{TextColors.BOLD}System Information:{TextColors.ENDC}")
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print(f"Current Directory: {os.getcwd()}")
        
        # API Configuration
        print(f"\n{TextColors.BOLD}API Configuration:{TextColors.ENDC}")
        print(f"Google API Key: {self.google_api_key[:4]}...{self.google_api_key[-4:] if len(self.google_api_key) > 8 else ''}")
        print(f"Google CSE ID: {self.google_cse_id}")
        
        # Browser status
        if BROWSER_AVAILABLE:
            print(f"\n{TextColors.BOLD}Browser Automation:{TextColors.ENDC}")
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            if openai_key:
                masked_key = f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else ""
                print(f"OpenAI API Key: {masked_key}")
                if self.browser and self.browser.browser_initialized:
                    print(f"Browser Status: Initialized and ready")
                else:
                    print(f"Browser Status: Not initialized")
            else:
                print(f"OpenAI API Key: Not set (required for browser automation)")
                print(f"Browser Status: Not available until OpenAI API key is set")
        
        # Shell Status
        print(f"\n{TextColors.BOLD}Shell Status:{TextColors.ENDC}")
        print(f"Active Shell: {self.current_shell_id}")
        print(f"Working Directory: {self.active_shells[self.current_shell_id]['cwd']}")
        
        # Usage Statistics
        current_time = time.time()
        uptime = current_time - self.last_command_time
        print(f"\n{TextColors.BOLD}Usage Statistics:{TextColors.ENDC}")
        print(f"Commands Processed: {len(self.command_history)}")
        print(f"Time Since Last Command: {uptime:.2f} seconds")
    
    def show_help(self) -> None:
        """Show help information"""
        print(f"\n{TextColors.HEADER}Sohay Assistant Help{TextColors.ENDC}")
        print("====================")
        
        print(f"\n{TextColors.BOLD}Basic Commands:{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}help{TextColors.ENDC} - Show this help message")
        print(f"  {TextColors.BLUE}exit{TextColors.ENDC}, {TextColors.BLUE}quit{TextColors.ENDC} - Exit the assistant")
        print(f"  {TextColors.BLUE}clear{TextColors.ENDC}, {TextColors.BLUE}cls{TextColors.ENDC} - Clear the screen")
        print(f"  {TextColors.BLUE}status{TextColors.ENDC} - Show the current status of the assistant")
        print(f"  {TextColors.BLUE}pwd{TextColors.ENDC} - Show the current working directory")
        
        print(f"\n{TextColors.BOLD}Google Search:{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}search for [query]{TextColors.ENDC} - Search for information")
        print(f"  {TextColors.BLUE}find [query]{TextColors.ENDC} - Alternative search command")
        print(f"  {TextColors.BLUE}search for [query] from past [hour/day/week/month/year]{TextColors.ENDC} - Search with date filter")
        print(f"  {TextColors.BLUE}setup google{TextColors.ENDC} - Configure Google Search API settings")
        
        # Show browser commands if available
        if BROWSER_AVAILABLE:
            print(f"\n{TextColors.BOLD}Browser Automation:{TextColors.ENDC}")
            print(f"  {TextColors.BLUE}browse [url]{TextColors.ENDC} - Open a website and interact with it")
            print(f"  {TextColors.BLUE}websearch [query]{TextColors.ENDC} - Search the web with browser")
            print(f"  {TextColors.BLUE}screenshot [filename]{TextColors.ENDC} - Take a screenshot of the current page")
            print(f"  {TextColors.BLUE}setup openai{TextColors.ENDC} - Configure OpenAI API key for browser automation")
            print(f"  {TextColors.BLUE}test openai{TextColors.ENDC} - Test if your OpenAI API key is working")
        
        print(f"\n{TextColors.BOLD}File Operations:{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}read [file]{TextColors.ENDC}, {TextColors.BLUE}open [file]{TextColors.ENDC} - Read file contents")
        print(f"  {TextColors.BLUE}cat [file]{TextColors.ENDC}, {TextColors.BLUE}type [file]{TextColors.ENDC} - Alternative file reading commands")
        
        print(f"\n{TextColors.BOLD}Shell Commands:{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}execute [command]{TextColors.ENDC}, {TextColors.BLUE}run [command]{TextColors.ENDC} - Run a shell command")
        print(f"  {TextColors.BLUE}> [command]{TextColors.ENDC} - Shorthand for shell commands")
        print(f"  {TextColors.BLUE}cd [directory]{TextColors.ENDC} - Change the current directory")
        
        print(f"\n{TextColors.BOLD}Examples:{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}search for latest AI news{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}read README.md{TextColors.ENDC}")
        print(f"  {TextColors.BLUE}execute ls -la{TextColors.ENDC}")
        if BROWSER_AVAILABLE:
            print(f"  {TextColors.BLUE}browse github.com/browser-use/browser-use{TextColors.ENDC}")
            print(f"  {TextColors.BLUE}websearch climate change latest research{TextColors.ENDC}")
    
    async def process_user_input_async(self, user_input: str) -> bool:
        """Process user input asynchronously (for browser commands)"""
        # Skip empty input
        if not user_input.strip():
            return True
            
        # Parse the input to determine what to do
        parsed = self.parse_tool_call(user_input)
        
        if parsed is None:
            # General response for inputs that don't match patterns
            print(f"\n{TextColors.YELLOW}I'm not sure how to process that request. Try these commands:{TextColors.ENDC}")
            print(f"- {TextColors.BLUE}search for [topic]{TextColors.ENDC}")
            print(f"- {TextColors.BLUE}read [file]{TextColors.ENDC}")
            print(f"- {TextColors.BLUE}execute [command]{TextColors.ENDC} or {TextColors.BLUE}> [command]{TextColors.ENDC}")
            if BROWSER_AVAILABLE:
                print(f"- {TextColors.BLUE}browse [url]{TextColors.ENDC}")
            print(f"- {TextColors.BLUE}help{TextColors.ENDC} for more information")
            return True
        
        # Handle browser commands
        if "browser" in parsed:
            command = parsed["browser"]
            args = parsed.get("args", {})
            print(f"\n{TextColors.GREEN}Executing browser command: {command}{TextColors.ENDC}")
            result = await self.execute_browser_command(command, args)
            print(f"\n{result}")
            return True
            
        # Handle system commands
        if "system" in parsed:
            if parsed["system"] == "exit":
                # Close browser if active
                if BROWSER_AVAILABLE and self.browser:
                    try:
                        await self.browser.close_browser()
                    except:
                        pass
                print(f"{TextColors.GREEN}Goodbye! Entering standby mode.{TextColors.ENDC}")
                return False
            elif parsed["system"] == "help":
                self.show_help()
                return True
            elif parsed["system"] == "setup_google":
                self.configure_google_api()
                return True
            elif parsed["system"] == "setup_openai":
                self.configure_openai_api()
                return True
            elif parsed["system"] == "test_openai":
                self.test_openai_api()
                return True
            elif parsed["system"] == "test_browser":
                await self.test_browser()
                return True
            elif parsed["system"] == "clear":
                # Already handled by clearing the screen
                return True
            elif parsed["system"] == "status":
                self.show_status()
                return True
            elif parsed["system"] == "current_directory":
                cwd = self.active_shells[self.current_shell_id]["cwd"]
                print(f"Current directory: {TextColors.BLUE}{cwd}{TextColors.ENDC}")
                return True
        
        # Handle error messages
        if "error" in parsed:
            print(f"\n{TextColors.RED}{parsed['error']}{TextColors.ENDC}")
            return True
        
        # Execute the appropriate tool
        if "tool" in parsed and "params" in parsed:
            print(f"\n{TextColors.GREEN}I'll help you with that using the {parsed['tool']} tool.{TextColors.ENDC}")
            result = self.execute_tool(parsed["tool"], parsed["params"])
            print(f"\n{result}")
        
        return True
    
    def process_user_input(self, user_input: str) -> bool:
        """Process user input and respond accordingly - wrapper for async version"""
        return asyncio.run(self.process_user_input_async(user_input))
    
    def run(self) -> None:
        """Main interaction loop for the assistant"""
        # Print welcome message with logo if available
        logo_file = "sohay_logo.txt"
        if os.path.exists(logo_file):
            try:
                with open(logo_file, 'r') as f:
                    logo = f.read()
                print(f"{TextColors.BLUE}{logo}{TextColors.ENDC}")
            except:
                # If logo can't be loaded, fall back to simple header
                print(f"{TextColors.HEADER}Sohay AI Assistant{TextColors.ENDC}")
        else:
            print(f"{TextColors.HEADER}Sohay AI Assistant{TextColors.ENDC}")
            
        print(f"{TextColors.GREEN}Type 'help' to see capabilities, 'exit' to quit{TextColors.ENDC}")
        print(f"Try commands like 'search for news about AI', 'read README.md', or '> ls -la'")
        
        print(f"\n{TextColors.YELLOW}Google Search API is pre-configured with your provided key.{TextColors.ENDC}")
        print(f"You can customize it further by typing 'setup google'.")
        
        # Start autonomous agent if available
        if AGENT_AVAILABLE and self.agent:
            response = input(f"Would you like to enable autonomous agent mode? (y/n): ").lower()
            if response.startswith('y'):
                self.agent.enable_autonomous_mode()
                self.start_agent_thread()
        
        running = True
        while running:
            try:
                user_input = input(f"\n{TextColors.BOLD}You:{TextColors.ENDC} ")
                running = self.process_user_input(user_input)
            except KeyboardInterrupt:
                print(f"\n{TextColors.YELLOW}Interrupted. Type 'exit' to quit.{TextColors.ENDC}")
            except Exception as e:
                print(f"\n{TextColors.RED}Error processing input: {str(e)}{TextColors.ENDC}")
                # Continue running despite errors

    async def test_browser(self) -> None:
        """Test the browser integration with a simple task"""
        if not BROWSER_AVAILABLE:
            print(f"{TextColors.RED}Browser automation module not available{TextColors.ENDC}")
            print("Please install the required dependencies with:")
            print("pip install browser-use playwright langchain langchain-openai python-dotenv")
            print("python -m playwright install")
            return
            
        if not self.browser:
            self.browser = SohayBrowser()
            
        print(f"\n{TextColors.HEADER}Browser Integration Test{TextColors.ENDC}")
        print("=========================")
        
        # Check if OpenAI API key is available
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key:
            print(f"{TextColors.RED}OpenAI API key not set. Browser automation requires an API key.{TextColors.ENDC}")
            print("Please set your API key with the 'setup openai' command.")
            return
            
        # Try to initialize the browser
        print(f"\n{TextColors.YELLOW}Initializing browser...{TextColors.ENDC}")
        init_result = await self.browser.initialize_browser()
        
        if "Error" in init_result:
            print(f"{TextColors.RED}{init_result}{TextColors.ENDC}")
            return
            
        print(f"{TextColors.GREEN}{init_result}{TextColors.ENDC}")
        
        # Run a simple browser task as a test
        print(f"\n{TextColors.YELLOW}Testing browser with a simple task...{TextColors.ENDC}")
        try:
            result = await self.browser.browse("Go to https://www.wikipedia.org and search for 'Artificial Intelligence'")
            print(f"\n{TextColors.GREEN}{result}{TextColors.ENDC}")
            
            # Close the browser
            await self.browser.close_browser()
            
            print(f"\n{TextColors.GREEN}Browser test completed successfully!{TextColors.ENDC}")
            print("You can now use browser automation features in Sohay.")
            print("Try commands like:")
            print("- browse [url]")
            print("- websearch [query]")
            print("- screenshot [filename]")
        except Exception as e:
            print(f"\n{TextColors.RED}Error during browser test: {str(e)}{TextColors.ENDC}")
            print("Please check your setup and try again.")

    def start_agent_thread(self) -> None:
        """Start the autonomous agent background thread"""
        if not AGENT_AVAILABLE or not self.agent:
            print(f"{TextColors.RED}Autonomous agent not available{TextColors.ENDC}")
            return
        
        if self.agent_thread and self.agent_thread.is_alive():
            print(f"{TextColors.YELLOW}Autonomous agent already running{TextColors.ENDC}")
            return
        
        self.agent_running = True
        self.agent_thread = threading.Thread(target=self.agent_thread_function)
        self.agent_thread.daemon = True  # Make thread terminate when main program exits
        self.agent_thread.start()
        print(f"{TextColors.GREEN}Autonomous agent started in background{TextColors.ENDC}")
    
    def stop_agent_thread(self) -> None:
        """Stop the autonomous agent background thread"""
        if not self.agent_thread:
            print(f"{TextColors.YELLOW}Autonomous agent not running{TextColors.ENDC}")
            return
        
        self.agent_running = False
        # Thread will terminate gracefully during next iteration
        print(f"{TextColors.GREEN}Autonomous agent will stop soon{TextColors.ENDC}")
    
    def agent_thread_function(self) -> None:
        """Background thread function for autonomous agent operation"""
        print(f"{TextColors.BLUE}Autonomous agent thread started{TextColors.ENDC}")
        
        while self.agent_running:
            try:
                # Run the agent's autonomous function
                result = asyncio.run(self.agent.run_autonomously())
                
                # Only print if something meaningful happened
                if result and "Waiting for next" not in result:
                    print(f"\n{TextColors.BLUE}[Autonomous Agent]{TextColors.ENDC} {result}")
                    print("\nYou: ", end="", flush=True)
                
            except Exception as e:
                print(f"\n{TextColors.RED}Error in autonomous agent: {str(e)}{TextColors.ENDC}")
            
            # Sleep to prevent CPU hogging
            time.sleep(5)
        
        print(f"{TextColors.BLUE}Autonomous agent thread stopped{TextColors.ENDC}")

    def handle_command(self, command: str) -> str:
        """Handle a command received from the user."""
        command = command.strip()
        
        if command == "help":
            return self.help_command()
        
        if command == "exit" or command == "quit":
            print("Goodbye!")
            # Stop agent thread if running
            if self.agent_running:
                self.stop_agent_thread()
            sys.exit(0)
        
        if command.startswith("browser"):
            # Browser commands
            if not BROWSER_AVAILABLE:
                return f"Browser functionality is not available. Error: {BROWSER_ERROR}\nPlease install browser-use with: pip install browser-use playwright langchain langchain-openai python-dotenv"
            
            return self.handle_browser_command(command)
        
        if command.startswith("agent") or command.startswith("auto"):
            # Agent commands
            if not AGENT_AVAILABLE:
                return "Autonomous agent functionality is not available.\nPlease ensure sohay_agent.py is in the same directory."
            
            # Strip "agent" prefix if present
            if command.startswith("agent "):
                agent_command = command[6:]
            else:
                agent_command = command
            
            # Handle agent start/stop commands
            if agent_command == "start":
                self.start_agent_thread()
                return "Autonomous agent started in background."
            elif agent_command == "stop":
                self.stop_agent_thread()
                return "Autonomous agent stopped."
            
            # Pass other commands to the agent handler
            return self.agent.handle_command(agent_command)
        
        if command == "test openai":
            # Test OpenAI API key
            if BROWSER_AVAILABLE:
                browser = SohayBrowser()
                return browser.test_openai_api()
            else:
                return "Browser module not available, but we can test the OpenAI API directly."
                # Implement direct API test here if needed
        
        if command == "test browser":
            # Test browser functionality
            if not BROWSER_AVAILABLE:
                return f"Browser functionality is not available. Error: {BROWSER_ERROR}\nPlease install browser-use with: pip install browser-use playwright langchain langchain-openai python-dotenv"
            
            # Create an async function and run it
            async def test_browser():
                browser = SohayBrowser()
                init_result = await browser.initialize_browser()
                if "Error" in init_result:
                    return init_result
                
                result = await browser.browse("Go to https://www.wikipedia.org and search for 'Artificial Intelligence'")
                close_result = await browser.close_browser()
                return f"Browser test completed: {result}\n{close_result}"
            
            return asyncio.run(test_browser())
        
        # If no command matched, treat as a message to the AI
        return self.handle_user_message(command)

    def help_command(self) -> str:
        """Show help information."""
        base_help = """
Sohay AI Assistant - Help

Commands:
- help: Show this help message
- exit/quit: Exit the assistant

Browser Commands (if browser-use is installed):
- browser open [URL]: Open a URL in the browser
- browser search [query]: Search the web for information
- browser browse [task]: Perform a complex browsing task
- browser screenshot [filename]: Take a screenshot of the current page
- browser close: Close the browser
- test browser: Test browser functionality
- test openai: Test if your OpenAI API key is working
"""

        # Add agent commands if available
        if AGENT_AVAILABLE:
            agent_help = """
Autonomous Agent Commands:
- agent start: Start the autonomous agent in background
- agent stop: Stop the autonomous agent
- auto on / enable autonomous: Enable autonomous mode
- auto off / disable autonomous: Disable autonomous mode
- add task [description] priority:[1-5] deadline:[time]: Add a new task
- list tasks: Show all tasks
- activate task [id/number]: Set a task as active
- complete task [id/number]: Mark a task as completed
- delete task [id/number]: Delete a task
- agent status: Show the agent's current status
"""
            base_help += agent_help

        base_help += "\nJust type your message to chat with Sohay AI Assistant."
        
        return base_help


def main():
    """Main function to initialize and run Sohay"""
    parser = argparse.ArgumentParser(description="Sohay AI Assistant Runner")
    parser.add_argument("--config", default="sohay.json", help="Path to the config file")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()
    
    # Create and run the assistant
    assistant = SohayAssistant(config_path=args.config)
    assistant.run()


if __name__ == "__main__":
    main() 