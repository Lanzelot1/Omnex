# Architecture Overview

This document provides a comprehensive overview of Omnex's architecture, design decisions, and system components.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                              │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────┤
│   ChatGPT   │   Claude    │   Gemini    │  Other LLMs │  Custom    │
│  (via API)  │ (via MCP)   │  (via API)  │  (via API)  │   Apps     │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬─────┘
       │             │             │             │             │
       └─────────────┴─────────────┴─────────────┴─────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      Protocol Layer         │
                    ├─────────────┬───────────────┤
                    │   RESTful   │     MCP       │
                    │     API     │   Server      │
                    └──────┬──────┴───────┬───────┘
                           │              │
                    ┌──────▼──────────────▼──────┐
                    │      Omnex Core Layer      │
                    ├─────────────────────────────┤
                    │  • Context Management       │
                    │  • Memory Storage           │
                    │  • Semantic Search          │
                    │  • Access Control           │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      Service Layer          │
                    ├─────────────┬───────────────┤
                    │   Business  │  Background   │
                    │    Logic    │    Tasks      │
                    └──────┬──────┴───────┬───────┘
                           │              │
                    ┌──────▼──────────────▼──────┐
                    │     Data Layer              │
                    ├─────────────┬───────────────┤
                    │ PostgreSQL  │    Redis      │
                    │  (Primary)  │ (Cache/Queue) │
                    └─────────────┴───────────────┘
```

## Core Components

### 1. API Gateway (FastAPI)

**Location**: `src/main.py`, `src/api/`

The REST API serves as the primary interface for external applications:

- **Framework**: FastAPI for high performance and automatic OpenAPI documentation
- **Middleware**: CORS, rate limiting, authentication (future)
- **Routing**: Version-based routing (`/api/v1/`)
- **Validation**: Pydantic models for request/response validation

**Key Design Decisions**:
- Async-first for better concurrency
- Automatic API documentation generation
- Type hints throughout for better developer experience

### 2. MCP Server

**Location**: `src/mcp/server.py`

The Model Context Protocol server enables direct AI assistant integration:

- **Protocol**: Anthropic's MCP standard
- **Transport**: STDIO for process communication
- **Tools**: Exposed as callable functions for AI assistants
- **Stateless**: Each tool call is independent

**Key Design Decisions**:
- Tool-based interface for AI-friendly interaction
- JSON schema validation for tool parameters
- Extensible design for adding new tools

### 3. Data Models

**Location**: `src/models/`

Two primary data models serve different use cases:

#### Context Model
```python
class Context:
    id: str                # Unique identifier
    namespace: str         # Logical grouping
    key: str              # Unique within namespace
    value: dict           # Arbitrary JSON data
    tags: List[str]       # Categorization
    created_at: datetime
    updated_at: datetime
```

**Use Cases**:
- Structured data storage
- Key-based retrieval
- Project/namespace organization

#### Memory Model
```python
class Memory:
    id: str                    # Unique identifier
    content: str              # Natural language text
    embedding: List[float]    # Vector representation
    metadata: dict            # Additional data
    created_at: datetime
```

**Use Cases**:
- Unstructured text storage
- Semantic search
- AI conversation history

### 4. Service Layer

**Location**: `src/services/` (to be implemented)

Business logic separated from API endpoints:

- **ContextService**: CRUD operations for contexts
- **MemoryService**: Memory storage and search
- **EmbeddingService**: Generate embeddings for semantic search
- **AuthService**: Authentication and authorization (future)

### 5. Background Tasks (Celery)

**Location**: `src/tasks/` (to be implemented)

Asynchronous task processing:

- **Embedding Generation**: Process text to vectors
- **Batch Operations**: Bulk import/export
- **Cleanup Tasks**: Data maintenance
- **Notifications**: Webhook deliveries

**Infrastructure**:
- Broker: Redis
- Result Backend: Redis
- Monitoring: Flower UI

### 6. Data Storage

#### PostgreSQL (Primary Database)
- **Purpose**: Persistent storage for all data
- **Features**: ACID compliance, full-text search, JSON support
- **Tables**:
  - `contexts`: Structured context storage
  - `memories`: Unstructured memory storage
  - `users`: User accounts (future)
  - `api_keys`: Authentication tokens (future)

#### Redis (Cache & Message Broker)
- **Purpose**: Caching and message queuing
- **Use Cases**:
  - API response caching
  - Session storage
  - Celery task queue
  - Rate limiting counters

## Data Flow

### 1. Context Storage Flow
```
Client Request → API Validation → Context Service → PostgreSQL
                                                    ↓
Client Response ← API Response ← Service Result ← Success/Error
```

### 2. Memory Search Flow
```
Search Query → API → Memory Service → Embedding Service
                                     ↓
                            Vector Similarity Search
                                     ↓
                            Ranked Results ← PostgreSQL
```

### 3. MCP Tool Call Flow
```
AI Assistant → MCP Client → STDIO → MCP Server
                                    ↓
                             Tool Handler
                                    ↓
                          Omnex Core Services
                                    ↓
                             JSON Response
```

## Scalability Considerations

### Horizontal Scaling
- **API Servers**: Stateless design allows multiple instances
- **MCP Servers**: Independent processes can be distributed
- **Background Workers**: Celery workers scale horizontally
- **Load Balancing**: Nginx/HAProxy for request distribution

### Vertical Scaling
- **Database**: PostgreSQL read replicas for read-heavy workloads
- **Caching**: Redis cluster for distributed caching
- **Connection Pooling**: Configured for optimal resource usage

### Performance Optimizations
- **Database Indexes**: On namespace, key, and timestamp fields
- **Query Optimization**: Prepared statements and query planning
- **Caching Strategy**: Cache-aside pattern for frequently accessed data
- **Async I/O**: Non-blocking operations throughout

## Security Architecture

### Authentication & Authorization (Future)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Key    │────▶│    JWT      │
│             │     │ Validation  │     │ Generation  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                         ┌─────▼─────┐
                                         │  Request  │
                                         │   Auth    │
                                         └───────────┘
```

### Data Protection
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS/SSL for all connections
- **Input Validation**: Pydantic models prevent injection
- **Rate Limiting**: Prevent abuse and DDoS

## Deployment Architecture

### Development Environment
```yaml
services:
  app:        # FastAPI application
  db:         # PostgreSQL database
  redis:      # Redis cache/broker
  mcp-server: # MCP server
  worker:     # Celery worker
  flower:     # Celery monitoring
```

### Production Environment (Recommended)
```
┌─────────────────┐
│   Load Balancer │
└────────┬────────┘
         │
┌────────▼────────┬─────────────┬─────────────┐
│   API Server 1  │ API Server 2 │ API Server N │
└────────┬────────┴──────┬──────┴──────┬──────┘
         │               │              │
         └───────────────┴──────────────┘
                         │
                ┌────────▼────────┐
                │   PostgreSQL    │
                │   (Primary)     │
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌────▼────┐ ┌───────▼───────┐
│  Read Replica 1 │ │  Redis  │ │ Read Replica N │
└─────────────────┘ └─────────┘ └───────────────┘
```

## Monitoring & Observability

### Metrics (Prometheus)
- API request latency
- Database query performance
- Cache hit rates
- Background task queue depth

### Logging (Structured)
- Application logs: JSON format
- Access logs: Request/response tracking
- Error logs: Exception tracking
- Audit logs: Security events

### Tracing (Future)
- Distributed tracing with OpenTelemetry
- Request flow visualization
- Performance bottleneck identification

## Future Architecture Enhancements

### 1. Multi-Tenancy
- Tenant isolation at database level
- Per-tenant resource quotas
- Separate namespaces per tenant

### 2. Event Streaming
- Kafka/RabbitMQ for event bus
- Real-time updates via WebSocket
- Event sourcing for audit trail

### 3. Machine Learning Pipeline
- Dedicated ML service
- Custom embedding models
- Fine-tuning capabilities

### 4. Federation
- Cross-instance data sharing
- Distributed search
- Privacy-preserving protocols

## Development Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Don't Repeat Yourself**: Shared utilities and services
3. **SOLID Principles**: Extensible and maintainable code
4. **12-Factor App**: Cloud-native best practices
5. **API-First Design**: Clear contracts between components

## Conclusion

Omnex's architecture is designed to be:
- **Scalable**: Handles growth in users and data
- **Extensible**: Easy to add new features
- **Maintainable**: Clear structure and documentation
- **Secure**: Defense in depth approach
- **Performant**: Optimized for AI workloads

The modular design allows teams to work independently on different components while maintaining system coherence through well-defined interfaces.