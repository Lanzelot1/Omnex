# API Reference

This document provides a comprehensive reference for the Omnex REST API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API is open for development. Authentication will be implemented in future versions using JWT tokens.

Future authentication header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Health Check

#### GET /health
Returns the health status of the application and its dependencies.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-06T12:00:00Z",
  "version": "0.1.0",
  "environment": "development",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "mcp_server": "healthy"
  }
}
```

#### GET /health/live
Kubernetes liveness probe endpoint.

**Response**
```json
{
  "status": "alive"
}
```

#### GET /health/ready
Kubernetes readiness probe endpoint.

**Response**
```json
{
  "status": "ready"
}
```

### Context Management

Contexts are key-value pairs organized by namespaces, designed for structured data storage and retrieval.

#### POST /api/v1/context/
Create a new context.

**Request Body**
```json
{
  "namespace": "project_name",
  "key": "requirements",
  "value": {
    "description": "Any JSON object",
    "priority": "high"
  },
  "tags": ["optional", "array", "of", "tags"]
}
```

**Response** (201 Created)
```json
{
  "id": "ctx_123456",
  "namespace": "project_name",
  "key": "requirements",
  "value": {
    "description": "Any JSON object",
    "priority": "high"
  },
  "tags": ["optional", "array", "of", "tags"],
  "created_at": "2024-01-06T12:00:00Z",
  "updated_at": "2024-01-06T12:00:00Z"
}
```

#### GET /api/v1/context/{namespace}
List all contexts in a namespace.

**Query Parameters**
- `tags` (optional): Filter by tags (comma-separated)
- `limit` (optional): Maximum results to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response**
```json
[
  {
    "id": "ctx_123456",
    "namespace": "project_name",
    "key": "requirements",
    "value": {...},
    "tags": ["tag1", "tag2"],
    "created_at": "2024-01-06T12:00:00Z",
    "updated_at": "2024-01-06T12:00:00Z"
  }
]
```

#### GET /api/v1/context/{namespace}/{key}
Retrieve a specific context.

**Response**
```json
{
  "id": "ctx_123456",
  "namespace": "project_name",
  "key": "requirements",
  "value": {
    "description": "Stored data"
  },
  "tags": ["tag1", "tag2"],
  "created_at": "2024-01-06T12:00:00Z",
  "updated_at": "2024-01-06T12:00:00Z"
}
```

#### DELETE /api/v1/context/{namespace}/{key}
Delete a specific context.

**Response** (204 No Content)

### Memory Management

Memories are unstructured text data with optional embeddings for semantic search.

#### POST /api/v1/memory/
Store a new memory.

**Request Body**
```json
{
  "content": "The user prefers TypeScript for frontend development",
  "metadata": {
    "source": "conversation",
    "confidence": 0.95
  },
  "embedding": [0.1, 0.2, 0.3, ...]  // Optional
}
```

**Response** (201 Created)
```json
{
  "id": "mem_123456",
  "content": "The user prefers TypeScript for frontend development",
  "metadata": {
    "source": "conversation",
    "confidence": 0.95
  },
  "created_at": "2024-01-06T12:00:00Z"
}
```

#### POST /api/v1/memory/search
Search for similar memories using semantic search.

**Request Body**
```json
{
  "query": "What programming languages does the user prefer?",
  "limit": 10,
  "threshold": 0.7
}
```

**Response**
```json
[
  {
    "id": "mem_123456",
    "content": "The user prefers TypeScript for frontend development",
    "metadata": {...},
    "created_at": "2024-01-06T12:00:00Z",
    "similarity_score": 0.92
  }
]
```

#### GET /api/v1/memory/{memory_id}
Retrieve a specific memory by ID.

**Response**
```json
{
  "id": "mem_123456",
  "content": "Memory content",
  "metadata": {...},
  "created_at": "2024-01-06T12:00:00Z"
}
```

#### DELETE /api/v1/memory/{memory_id}
Delete a specific memory.

**Response** (204 No Content)

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "namespace"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

When rate limiting is enabled (`RATE_LIMIT_ENABLED=true`), the following headers are included in responses:

- `X-RateLimit-Limit`: Request limit per minute
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when the limit resets

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```
GET /api/v1/context/my_namespace?limit=20&offset=40
```

## Interactive Documentation

When running locally, you can access interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to test API endpoints directly from your browser.

## SDK Examples

### Python
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Create context
response = client.post(
    "/api/v1/context/",
    json={
        "namespace": "my_app",
        "key": "settings",
        "value": {"theme": "dark"}
    }
)
```

### JavaScript/TypeScript
```typescript
const response = await fetch('http://localhost:8000/api/v1/context/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    namespace: 'my_app',
    key: 'settings',
    value: { theme: 'dark' }
  })
});
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/context/ \
  -H "Content-Type: application/json" \
  -d '{"namespace":"my_app","key":"settings","value":{"theme":"dark"}}'
```