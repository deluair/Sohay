# Sohay AI Assistant

Sohay is an advanced autonomous AI agent designed to work independently on tasks with minimal user intervention.

![Sohay Banner](landing/img/sohay-banner.png)

## Features

- **Free Web Search**: Gather information from the web without requiring API keys
- **Enhanced Planning**: Context-aware planning that creates detailed execution strategies
- **Task Dependencies**: Handle complex workflows with interdependent tasks
- **Long-term Memory**: Store and retrieve insights across sessions
- **Task Scheduling**: Schedule recurring tasks (minutes, hourly, daily, weekly, monthly)
- **Browser Automation**: Control web browsers for research and data gathering

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Required packages (install with `pip install -r requirements.txt`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sohay.git
   cd sohay
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For browser automation features:
   ```bash
   pip install browser-use playwright langchain langchain-openai python-dotenv
   python -m playwright install
   ```

### Running Sohay

Start the assistant with:
```bash
python sohay_runner.py
```

## Using Sohay

### Basic Commands

- `help`: Show available commands and capabilities
- `exit` or `quit`: Exit the assistant

### Autonomous Agent Commands

- `auto on` or `enable autonomous`: Enable autonomous mode
- `auto off` or `disable autonomous`: Disable autonomous mode
- `add task [description] priority:[1-5] deadline:[time]`: Add a new task
- `list tasks`: Show all tasks with their status
- `activate task [id]`: Set a specific task as active
- `complete task [id]`: Mark a task as completed
- `delete task [id]`: Delete a task
- `agent status`: Show the current status of the agent

#### Task Examples

```
You: add task Research quantum computing advancements priority:3 deadline:tomorrow
You: add task Write summary report depends:1 priority:2
You: add task Monitor for new papers schedule:daily:1
```

### Browser Commands

- `browser open [URL]`: Open a website in the browser
- `browser search [query]`: Search the web for information
- `browser browse [task]`: Perform a complex browsing task described in natural language
- `test browser`: Test browser automation functionality

## Architecture

Sohay consists of several key components:

1. **Core Runner** (`sohay_runner.py`): The main interface for user interaction
2. **Autonomous Agent** (`sohay_agent.py`): Manages tasks and autonomous operation
3. **Browser Module** (`sohay_browser.py`): Handles web browsing and automation
4. **Search Module** (`sohay_search.py`): Provides web search capabilities

## Dependencies

- `browser-use`: For browser automation
- `playwright`: For controlling web browsers
- `langchain`/`langchain-openai`: For language model integration
- `python-dotenv`: For managing environment variables
- `beautifulsoup4`: For parsing web content

## Documentation

For more detailed documentation, see:
- [AUTONOMOUS_AGENT.md](AUTONOMOUS_AGENT.md) - Details on the autonomous agent
- [BROWSER_INTEGRATION.md](BROWSER_INTEGRATION.md) - Browser automation details

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with the support of AI research and development tools
- Browser automation powered by [browser-use](https://github.com/browser-use/browser-use) 