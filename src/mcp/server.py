"""Simple MCP server example for Omnex."""

import asyncio
import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    LATEST_PROTOCOL_VERSION,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from src.core.logging import get_logger


logger = get_logger(__name__)


class MCPServer:
    """Omnex MCP Server implementation."""
    
    def __init__(self, name: str = "omnex-mcp"):
        """Initialize the MCP server."""
        self.name = name
        self.server = Server(name)
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="store_context",
                    description="Store context in Omnex memory layer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace for organizing contexts"
                            },
                            "key": {
                                "type": "string",
                                "description": "Unique key within namespace"
                            },
                            "value": {
                                "type": "object",
                                "description": "Context data to store"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags for categorization"
                            }
                        },
                        "required": ["namespace", "key", "value"]
                    }
                ),
                Tool(
                    name="retrieve_context",
                    description="Retrieve context from Omnex memory layer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to search in"
                            },
                            "key": {
                                "type": "string",
                                "description": "Key to retrieve"
                            }
                        },
                        "required": ["namespace", "key"]
                    }
                ),
                Tool(
                    name="search_memory",
                    description="Search for similar memories using semantic search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]] = None
        ) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "store_context":
                    result = await self._store_context(arguments or {})
                elif name == "retrieve_context":
                    result = await self._retrieve_context(arguments or {})
                elif name == "search_memory":
                    result = await self._search_memory(arguments or {})
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}", error=str(e))
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
        
    async def _store_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Store context in memory."""
        namespace = args.get("namespace")
        key = args.get("key")
        value = args.get("value")
        tags = args.get("tags", [])
        
        logger.info(
            "Storing context",
            namespace=namespace,
            key=key,
            tags=tags
        )
        
        # In a real implementation, this would store to a database
        return {
            "status": "success",
            "message": f"Context stored in {namespace}/{key}",
            "id": f"ctx_{namespace}_{key}",
            "tags": tags
        }
    
    async def _retrieve_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve context from memory."""
        namespace = args.get("namespace")
        key = args.get("key")
        
        logger.info(
            "Retrieving context",
            namespace=namespace,
            key=key
        )
        
        # Mock implementation
        return {
            "namespace": namespace,
            "key": key,
            "value": {
                "example": "This is example context data",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "tags": ["example", "test"]
        }
    
    async def _search_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories."""
        query = args.get("query")
        limit = args.get("limit", 10)
        
        logger.info("Searching memories", query=query, limit=limit)
        
        # Mock implementation
        return {
            "query": query,
            "results": [
                {
                    "id": "mem_1",
                    "content": f"Example result 1 for: {query}",
                    "similarity": 0.95
                },
                {
                    "id": "mem_2",
                    "content": f"Example result 2 for: {query}",
                    "similarity": 0.87
                }
            ],
            "total": 2
        }
    
    async def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        logger.info(f"Starting MCP server: {self.name}")
        
        # Run with the specified transport
        async with self.server.run(transport) as _:
            logger.info("MCP server running")
            # The server will run until interrupted
            await asyncio.Event().wait()


async def main():
    """Main entry point."""
    server = MCPServer("omnex-mcp")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())