# MCP Integration Guide

This guide explains how to integrate Omnex with AI assistants using the Model Context Protocol (MCP).

## What is MCP?

Model Context Protocol (MCP) is an open protocol introduced by Anthropic that provides a standard way for AI assistants to interact with external data sources and tools. Think of it as "USB-C for AI" - a universal connection standard that allows any AI assistant to plug into any data source.

## Why Use MCP with Omnex?

- **Standardized Interface**: Works with any MCP-compatible AI assistant
- **Tool-based Interaction**: AI assistants can directly store and retrieve memories
- **Stateful Context**: Maintain context across different conversations and AI models
- **Privacy-Focused**: Your data stays in your control

## MCP Server Setup

### 1. Start the Omnex MCP Server

```bash
# Using Make
make run-mcp

# Or directly
python -m src.mcp.server

# Or with Docker
docker-compose up mcp-server
```

The MCP server runs on port 3000 by default.

### 2. Available MCP Tools

Omnex provides three core tools through MCP:

#### store_context
Store structured context data with namespace/key organization.

```json
{
  "name": "store_context",
  "description": "Store context in Omnex memory layer",
  "inputSchema": {
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
}
```

#### retrieve_context
Retrieve specific context by namespace and key.

```json
{
  "name": "retrieve_context",
  "description": "Retrieve context from Omnex memory layer",
  "inputSchema": {
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
}
```

#### search_memory
Search for memories using semantic search.

```json
{
  "name": "search_memory",
  "description": "Search for similar memories using semantic search",
  "inputSchema": {
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
}
```

## Integration Examples

### Claude Desktop Integration

1. **Configure Claude Desktop**
   
   Add to your Claude Desktop configuration:
   ```json
   {
     "mcpServers": {
       "omnex": {
         "command": "python",
         "args": ["-m", "src.mcp.server"],
         "cwd": "/path/to/omnex"
       }
     }
   }
   ```

2. **Use in Conversation**
   
   Once configured, you can ask Claude to:
   - "Store this project's requirements in Omnex"
   - "What do you remember about our previous discussion?"
   - "Search for all contexts related to API design"

### Programmatic MCP Client

See `examples/mcp_client_example.py` for a complete example:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp.server"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Store context
            result = await session.call_tool(
                "store_context",
                arguments={
                    "namespace": "project_x",
                    "key": "architecture",
                    "value": {
                        "backend": "FastAPI",
                        "database": "PostgreSQL",
                        "frontend": "React"
                    },
                    "tags": ["technical", "architecture"]
                }
            )
            print("Stored:", result.content[0].text)
            
            # Retrieve context
            result = await session.call_tool(
                "retrieve_context",
                arguments={
                    "namespace": "project_x",
                    "key": "architecture"
                }
            )
            print("Retrieved:", result.content[0].text)
            
            # Search memories
            result = await session.call_tool(
                "search_memory",
                arguments={
                    "query": "What technology stack are we using?",
                    "limit": 5
                }
            )
            print("Search results:", result.content[0].text)

asyncio.run(main())
```

## Best Practices

### 1. Namespace Organization

Use meaningful namespaces to organize your contexts:
- `project_name` - For project-specific information
- `user_preferences` - For user settings and preferences
- `conversation_history` - For important conversation points
- `knowledge_base` - For reference information

### 2. Key Naming Conventions

Use clear, descriptive keys:
- `requirements` - Project requirements
- `architecture` - Technical architecture decisions
- `meeting_notes_2024_01_06` - Time-stamped information
- `user_profile` - User information

### 3. Tagging Strategy

Use tags to enable cross-namespace discovery:
- `#important` - Critical information
- `#decision` - Architectural or business decisions
- `#todo` - Action items
- `#reference` - Reference documentation

### 4. Context vs Memory

**Use Contexts for:**
- Structured data (JSON objects)
- Information you'll retrieve by exact key
- Configuration and settings
- Project documentation

**Use Memories for:**
- Natural language notes
- Information for semantic search
- Conversation summaries
- Insights and observations

## Advanced Usage

### Custom MCP Server Extensions

You can extend the MCP server with additional tools:

```python
# In src/mcp/server.py

@self.server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        # ... existing tools ...
        Tool(
            name="analyze_context",
            description="Analyze context patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"}
                },
                "required": ["namespace"]
            }
        )
    ]

async def _analyze_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
    namespace = args.get("namespace")
    # Your analysis logic here
    return {"analysis": "results"}
```

### Webhooks and Events

Future versions will support webhooks for real-time updates:

```python
# Coming soon
omnex.on_context_updated(namespace="project_x", callback=handle_update)
```

## Troubleshooting

### MCP Server Won't Start

1. Check port availability:
   ```bash
   lsof -i :3000
   ```

2. Verify Python environment:
   ```bash
   which python
   python --version  # Should be 3.9+
   ```

3. Check logs:
   ```bash
   python -m src.mcp.server 2>&1 | tee mcp.log
   ```

### Tools Not Appearing

1. Verify server is running:
   ```bash
   curl http://localhost:3000/health
   ```

2. Check MCP client configuration
3. Ensure proper path to Omnex directory

### Connection Errors

1. Check firewall settings
2. Verify localhost resolution
3. Try explicit 127.0.0.1 instead of localhost

## Next Steps

- Learn about [API Reference](../api-reference/) for direct HTTP access
- Explore [Architecture Overview](../architecture.md) for system design
- Check [examples/](../../examples/) for more integration examples