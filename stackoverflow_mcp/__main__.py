#!/usr/bin/env python
from stackoverflow_mcp.server import mcp

def main():
    """Entry point for the Stack Overflow MCP server."""
    print("Starting Stack Overflow MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main()