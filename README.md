# hmdl - Heimdall Observability SDK for Python

[![PyPI version](https://badge.fury.io/py/hmdl.svg)](https://badge.fury.io/py/hmdl)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Observability SDK for MCP (Model Context Protocol) servers, built on OpenTelemetry.

## Installation

```bash
pip install hmdl
```

## Quick Start

### 1. Create Organization and Project in Heimdall

Before using the SDK, you need to set up your organization and project in the Heimdall dashboard:

1. Start the Heimdall backend and frontend (see [Heimdall Documentation](https://docs.tryheimdall.com))
2. Navigate to http://localhost:5173
3. **Create an account** with your email and password
4. **Create an Organization** - this groups your projects together
5. **Create a Project** - each project has a unique ID for trace collection
6. Go to **Settings** to find your **Organization ID** and **Project ID**

### 2. Set up environment variables

```bash
# Required for local development
export HEIMDALL_ENDPOINT="http://localhost:4318"  # Your Heimdall backend
export HEIMDALL_ORG_ID="your-org-id"              # From Heimdall Settings page
export HEIMDALL_PROJECT_ID="your-project-id"      # From Heimdall Settings page
export HEIMDALL_ENABLED="true"

# Optional
export HEIMDALL_SERVICE_NAME="my-mcp-server"
export HEIMDALL_ENVIRONMENT="development"

# For production (with API key)
export HEIMDALL_API_KEY="your-api-key"
export HEIMDALL_ENDPOINT="https://api.heimdall.dev"
```

### 3. Initialize the client

```python
from hmdl import HeimdallClient

# Initialize (uses environment variables by default)
client = HeimdallClient()

# Or with explicit configuration
client = HeimdallClient(
    endpoint="http://localhost:4318",
    org_id="your-org-id",           # From Settings page
    project_id="your-project-id",   # From Settings page
    service_name="my-mcp-server",
    environment="development"
)
```

### 4. Instrument your MCP tool functions

```python
from hmdl import trace_mcp_tool

@trace_mcp_tool()
def search_documents(query: str, limit: int = 10) -> list:
    """Search for documents matching the query."""
    # Your implementation here
    return results

@trace_mcp_tool("custom-tool-name")
def another_tool(data: dict) -> dict:
    """Another MCP tool with custom name."""
    return {"processed": True, **data}
```

### 5. Async support

The decorator works with async functions:

```python
@trace_mcp_tool()
async def async_search(query: str) -> list:
    results = await database.search(query)
    return results
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `HEIMDALL_ENDPOINT` | Heimdall backend URL | `http://localhost:4318` |
| `HEIMDALL_ORG_ID` | Organization ID (from Settings page) | `default` |
| `HEIMDALL_PROJECT_ID` | Project ID (from Settings page) | `default` |
| `HEIMDALL_ENABLED` | Enable/disable tracing | `true` |
| `HEIMDALL_SERVICE_NAME` | Service name for traces | `mcp-server` |
| `HEIMDALL_ENVIRONMENT` | Deployment environment | `development` |
| `HEIMDALL_API_KEY` | API key (optional for local dev) | - |
| `HEIMDALL_DEBUG` | Enable debug logging | `false` |
| `HEIMDALL_BATCH_SIZE` | Spans per batch | `100` |
| `HEIMDALL_FLUSH_INTERVAL_MS` | Flush interval (ms) | `5000` |
| `HEIMDALL_SESSION_ID` | Default session ID | - |
| `HEIMDALL_USER_ID` | Default user ID | - |

### Local Development

For local development, you don't need an API key. Just set:

```bash
export HEIMDALL_ENDPOINT="http://localhost:4318"
export HEIMDALL_ORG_ID="your-org-id"          # Copy from Settings page
export HEIMDALL_PROJECT_ID="your-project-id"  # Copy from Settings page
export HEIMDALL_ENABLED="true"
```

## Advanced Usage

### Session and User Tracking

`trace_mcp_tool` automatically includes session and user IDs in spans. You just need to provide them via one of these methods:

#### Option 1: HTTP Headers (Recommended for MCP servers)

Pass HTTP headers directly to `trace_mcp_tool`. Session ID is extracted from the `Mcp-Session-Id` header, and user ID from the JWT token in the `Authorization` header:

```python
from hmdl import trace_mcp_tool

@app.post("/mcp")
def handle_request():
    @trace_mcp_tool(headers=dict(request.headers))
    def search_tool(query: str):
        return results

    return search_tool("test")  # Session/user included in span
```

#### Option 2: Extractors (Per-tool extraction)

```python
from typing import Optional

@trace_mcp_tool(
    session_extractor=lambda args, kwargs: kwargs.get('session_id'),
    user_extractor=lambda args, kwargs: kwargs.get('user_id'),
)
def my_tool(query: str, session_id: Optional[str] = None, user_id: Optional[str] = None):
    return f"Query: {query}"
```

#### Resolution Priority

1. Extractor callback → 2. HTTP headers → 3. Client value (initialized from environment variables)

> **Note**: If no user ID is found through any of these methods, `"anonymous"` is used as the default.

### Custom span names

```python
@trace_mcp_tool("custom-tool-name")
def my_tool():
    pass
```

### Manual spans

```python
from hmdl import HeimdallClient

client = HeimdallClient()

with client.start_span("my-operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your code here
```

### Flush on shutdown

```python
import atexit
from hmdl import HeimdallClient

client = HeimdallClient()

# Ensure spans are flushed on exit
atexit.register(client.flush)
```

## What gets tracked?

For each MCP function call, Heimdall tracks:

- **Input parameters**: Function arguments (serialized to JSON)
- **Output/response**: Return value (serialized to JSON)
- **Status**: Success or error
- **Latency**: Execution time in milliseconds
- **Errors**: Exception type, message, and stack trace
- **Metadata**: Service name, environment, timestamps

## OpenTelemetry Integration

This SDK is built on OpenTelemetry, making it compatible with the broader observability ecosystem. You can:

- Use existing OTel instrumentations alongside Heimdall
- Export to multiple backends simultaneously
- Leverage OTel's context propagation for distributed tracing

## License

MIT License - see [LICENSE](LICENSE) for details.

