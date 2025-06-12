#!/usr/bin/env python3
"""Download and setup sample data for development."""

import json
import os
from pathlib import Path


def create_sample_data():
    """Create sample data files for development."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Sample contexts
    sample_contexts = {
        "contexts": [
            {
                "namespace": "example_project",
                "key": "requirements",
                "value": {
                    "title": "AI Chat Application",
                    "description": "Build a conversational AI interface",
                    "features": [
                        "Natural language understanding",
                        "Context management",
                        "Multi-turn conversations"
                    ],
                    "deadline": "2024-06-01"
                },
                "tags": ["project", "requirements", "ai"]
            },
            {
                "namespace": "example_project",
                "key": "architecture",
                "value": {
                    "backend": "FastAPI + PostgreSQL",
                    "frontend": "React + TypeScript",
                    "ai_models": ["GPT-4", "Claude", "Llama"],
                    "deployment": "Kubernetes on AWS"
                },
                "tags": ["project", "architecture", "technical"]
            },
            {
                "namespace": "team_knowledge",
                "key": "best_practices",
                "value": {
                    "coding": [
                        "Use type hints in Python",
                        "Write comprehensive tests",
                        "Document all public APIs"
                    ],
                    "collaboration": [
                        "Create clear PR descriptions",
                        "Review code within 24 hours",
                        "Use conventional commits"
                    ]
                },
                "tags": ["team", "guidelines", "development"]
            }
        ]
    }
    
    # Sample memories
    sample_memories = {
        "memories": [
            {
                "id": "mem_001",
                "content": "The user prefers using TypeScript for all frontend development due to better type safety and IDE support.",
                "metadata": {
                    "source": "conversation",
                    "confidence": 0.95,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            },
            {
                "id": "mem_002",
                "content": "Previous projects have shown that microservices architecture works well for this team, especially with service mesh using Istio.",
                "metadata": {
                    "source": "project_retrospective",
                    "confidence": 0.88,
                    "timestamp": "2024-01-10T14:00:00Z"
                }
            },
            {
                "id": "mem_003",
                "content": "Performance optimization should focus on database queries first, as they account for 70% of response time in similar applications.",
                "metadata": {
                    "source": "performance_analysis",
                    "confidence": 0.92,
                    "timestamp": "2024-01-05T09:15:00Z"
                }
            }
        ]
    }
    
    # Write sample data files
    with open(data_dir / "sample_contexts.json", "w") as f:
        json.dump(sample_contexts, f, indent=2)
    
    with open(data_dir / "sample_memories.json", "w") as f:
        json.dump(sample_memories, f, indent=2)
    
    # Create sample MCP configuration
    mcp_config = {
        "mcpServers": {
            "omnex": {
                "command": "python",
                "args": ["-m", "src.mcp.server"],
                "env": {
                    "OMNEX_API_KEY": "your-api-key-here"
                }
            }
        }
    }
    
    with open(data_dir / "mcp_config.json", "w") as f:
        json.dump(mcp_config, f, indent=2)
    
    print("✅ Sample data created successfully!")
    print(f"📁 Data files created in: {data_dir.absolute()}")
    print("   - sample_contexts.json")
    print("   - sample_memories.json")
    print("   - mcp_config.json")


if __name__ == "__main__":
    create_sample_data()