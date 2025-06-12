"""Example of using Omnex MCP server with a client."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Example MCP client connecting to Omnex server."""
    
    # Create server parameters for stdio transport
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp.server"],
        env=None
    )
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Example 1: Store context
            print("\n--- Storing Context ---")
            result = await session.call_tool(
                "store_context",
                arguments={
                    "namespace": "project_x",
                    "key": "requirements",
                    "value": {
                        "description": "Build an AI chat interface",
                        "deadline": "2024-03-01",
                        "priority": "high"
                    },
                    "tags": ["project", "requirements", "ai"]
                }
            )
            print("Store result:", result.content[0].text)
            
            # Example 2: Retrieve context
            print("\n--- Retrieving Context ---")
            result = await session.call_tool(
                "retrieve_context",
                arguments={
                    "namespace": "project_x",
                    "key": "requirements"
                }
            )
            print("Retrieved:", result.content[0].text)
            
            # Example 3: Search memories
            print("\n--- Searching Memories ---")
            result = await session.call_tool(
                "search_memory",
                arguments={
                    "query": "AI chat interface requirements",
                    "limit": 5
                }
            )
            print("Search results:", result.content[0].text)


if __name__ == "__main__":
    print("Omnex MCP Client Example")
    print("=" * 40)
    asyncio.run(main())