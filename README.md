# <div align="center">Stack Overflow MCP Server</div>

<div align="center">

[![Python Version][python-badge]][python-url]
[![License][license-badge]][license-url]

</div>

This [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server enables AI assistants like Claude to search and access Stack Overflow content through a standardized protocol, providing seamless access to programming solutions, error handling, and technical knowledge.

> [!NOTE]
>
> The Stack Overflow MCP Server is currently in Beta. We welcome your feedback and encourage you to report any bugs by opening an issue.

## Features

- 🔍 **Multiple Search Methods**: Search by query, error message, or specific question ID
- 📊 **Advanced Filtering**: Filter results by tags, score, accepted answers, and more
- 🧩 **Stack Trace Analysis**: Parse and find solutions for error stack traces
- 📝 **Rich Formatting**: Get results in Markdown or JSON format
- 💬 **Comments Support**: Optionally include question and answer comments
- ⚡ **Rate Limiting**: Built-in protection to respect Stack Exchange API quotas

### Example Prompts and Use Cases

Here are some example prompts you can use with Claude when the Stack Overflow MCP server is integrated:

| Tool                  | Example Prompt                                                                       | Description                                                                      |
| --------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `search_by_query`     | "Search Stack Overflow for Django pagination best practices"                         | Finds the most relevant questions and answers about Django pagination techniques |
| `search_by_query`     | "Find Python asyncio examples with tags python and asyncio"                          | Searches for specific code examples filtering by multiple tags                   |
| `search_by_error`     | "Why am I getting 'TypeError: object of type 'NoneType' has no len()' in Python?"    | Finds solutions for a common Python error                                        |
| `get_question`        | "Get Stack Overflow question 53051465 about React hooks"                             | Retrieves a specific question by ID, including all answers                       |
| `analyze_stack_trace` | "Fix this error: ReferenceError: useState is not defined at Component in javascript" | Analyzes JavaScript error to find relevant solutions                             |
| `advanced_search`     | "Find highly rated answers about memory leaks in C++ with at least 10 upvotes"       | Uses advanced filtering to find high-quality answers                             |

## Prerequisites

Before using this MCP server, you need to:

1. Get a Stack Exchange API key (see below)
2. Have Python 3.10+ installed
3. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended)

### Getting a Stack Exchange API Key

To use this server effectively, you'll need a Stack Exchange API key:

1. Go to [Stack Apps OAuth Registration](https://stackapps.com/apps/oauth/register)
2. Fill out the form with your application details:
   - Name: "Stack Overflow MCP" (or your preferred name)
   - Description: "MCP server for accessing Stack Overflow"
   - OAuth Domain: "localhost" (for local usage)
   - Application Website: Your website or leave blank
3. Submit the form
4. Copy your API Key (shown as "Key" on the next page)

This API key is not considered a secret and may be safely embedded in client-side code or distributed binaries. It simply allows you to receive a higher request quota when making requests to the Stack Exchange API.

## Installation

### Installing from PyPI

[Stackoverflow PyPI page](https://pypi.org/project/stackoverflow-mcp/0.1.2/)

```bash
# Using pip
pip install stackoverflow-mcp

# OR Using uv
uv venv
uv pip install stackoverflow-mcp

# OR using uv wihtout an venv
uv pip install stackoverflow-mcp --system
```

### Installing from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/stackoverflow-mcp-server.git
cd stackoverflow-mcp-server

# Install with uv
uv venv
uv pip install -e .
```

### Adding to Claude Desktop

To run the Stack Overflow MCP server with Claude Desktop:

1. Download [Claude Desktop](https://claude.ai/download).

2. Launch Claude and navigate to: Settings > Developer > Edit Config.

3. Update your `claude_desktop_config.json` file with the following configuration:

```json
{
  "mcpServers": {
    "stack-overflow": {
      "command": "uv",
      "args": ["run", "-m", "stackoverflow_mcp"],
      "env": {
        "STACK_EXCHANGE_API_KEY": "your_API_key"
      }
    }
  }
}
```

You can also specify a custom directory:

```json
{
  "mcpServers": {
    "stack-overflow": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/stackoverflow-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "STACK_EXCHANGE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Configuration

### Environment Variables

The server can be configured using these environment variables:

```bash
# Required
STACK_EXCHANGE_API_KEY=your_api_key_here

# Optional
MAX_REQUEST_PER_WINDOW=30     # Maximum requests per rate limit window
RATE_LIMIT_WINDOW_MS=60000    # Rate limit window in milliseconds (1 minute)
RETRY_AFTER_MS=2000           # Delay after hitting rate limit
```

### Using a .env File

You can create a `.env` file in the project root:

```
STACK_EXCHANGE_API_KEY=your_api_key_here
MAX_REQUEST_PER_WINDOW=30
RATE_LIMIT_WINDOW_MS=60000
RETRY_AFTER_MS=2000
```

## Usage

### Available Tools

The Stack Overflow MCP server provides the following tools:

#### 1. search_by_query

Search Stack Overflow for questions matching a query.

```
Parameters:
- query: The search query
- tags: Optional list of tags to filter by (e.g., ["python", "pandas"])
- excluded_tags: Optional list of tags to exclude
- min_score: Minimum score threshold for questions
- has_accepted_answer: Whether questions must have an accepted answer
- include_comments: Whether to include comments in results
- response_format: Format of response ("json" or "markdown")
- limit: Maximum number of results to return
```

#### 2. search_by_error

Search Stack Overflow for solutions to an error message.

```
Parameters:
- error_message: The error message to search for
- language: Programming language (e.g., "python", "javascript")
- technologies: Related technologies (e.g., ["react", "django"])
- min_score: Minimum score threshold for questions
- include_comments: Whether to include comments in results
- response_format: Format of response ("json" or "markdown")
- limit: Maximum number of results to return
```

#### 3. get_question

Get a specific Stack Overflow question by ID.

```
Parameters:
- question_id: The Stack Overflow question ID
- include_comments: Whether to include comments in results
- response_format: Format of response ("json" or "markdown")
```

#### 4. analyze_stack_trace

Analyze a stack trace and find relevant solutions on Stack Overflow.

```
Parameters:
- stack_trace: The stack trace to analyze
- language: Programming language of the stack trace
- include_comments: Whether to include comments in results
- response_format: Format of response ("json" or "markdown")
- limit: Maximum number of results to return
```

#### 5. advanced_search

Advanced search for Stack Overflow questions with many filter options.

```
Parameters:
- query: Free-form search query
- tags: List of tags to filter by
- excluded_tags: List of tags to exclude
- min_score: Minimum score threshold
- title: Text that must appear in the title
- body: Text that must appear in the body
- answers: Minimum number of answers
- has_accepted_answer: Whether questions must have an accepted answer
- sort_by: Field to sort by (activity, creation, votes, relevance)
- include_comments: Whether to include comments in results
- response_format: Format of response ("json" or "markdown")
- limit: Maximum number of results to return
```

## Development

This section is for contributors who want to develop or extend the Stack Overflow MCP server.

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/stackoverflow-mcp-server.git
cd stackoverflow-mcp-server

# Install dev dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_formatter.py
pytest tests/test_server.py

# Run tests with coverage report
pytest --cov=stackoverflow_mcp
```

### Project Structure

```
stackoverflow-mcp-server/
├── stackoverflow_mcp/          # Main package
│   ├── __init__.py
|   |── __main__.py             # Entry point
│   ├── api.py                  # Stack Exchange API client
│   ├── env.py                  # Environment configuration
│   ├── formatter.py            # Response formatting utilities
│   ├── server.py               # MCP server implementation
│   └── types.py                # Data classes
├── tests/                      # Test suite
│   ├── api/
│   │   └── test_search.py      # API search tests
│   ├── test_formatter.py       # Formatter tests
│   ├── test_general_api_health.py  # API health tests
│   └── test_server.py          # Server tests
├── setup.py                    # Package configuration
├── LICENSE                     # License file
└── README.md                   # This file
```

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

Please make sure to update tests as appropriate and follow the project's coding style.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<p align="center">
Stack Overflow MCP Server: AI-accessible programming knowledge
</p>

<!-- Badges -->

[python-badge]: https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg
[python-url]: https://www.python.org/downloads/
[license-badge]: https://img.shields.io/badge/license-MIT-green.svg
[license-url]: LICENSE
