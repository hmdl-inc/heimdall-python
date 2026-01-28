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

### 1. Set up environment variables

```bash
export HEIMDALL_API_KEY="your-api-key"
export HEIMDALL_ENDPOINT="https://api.heimdall.dev"  # or your self-hosted instance
export HEIMDALL_SERVICE_NAME="my-mcp-server"
```

### 2. Initialize the client

```python
from hmdl import HeimdallClient

# Initialize (uses environment variables by default)
client = HeimdallClient()

# Or with explicit configuration
client = HeimdallClient(
    api_key="your-api-key",
    endpoint="https://api.heimdall.dev",
    service_name="my-mcp-server",
    environment="production"
)
```

### 3. Instrument your MCP functions

```python
from hmdl import trace_mcp_tool, trace_mcp_resource, trace_mcp_prompt, observe

# Trace MCP tool calls
@trace_mcp_tool()
def search_documents(query: str, limit: int = 10) -> list:
    """Search for documents matching the query."""
    # Your implementation here
    return results

# Trace MCP resource access
@trace_mcp_resource()
def read_file(uri: str) -> str:
    """Read a file resource."""
    with open(uri) as f:
        return f.read()

# Trace MCP prompt generation
@trace_mcp_prompt()
def generate_summary_prompt(context: str) -> list:
    """Generate a summary prompt."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Summarize: {context}"}
    ]

# General observation for any function
@observe
def process_data(data: dict) -> dict:
    """Process some data."""
    return {"processed": True, **data}
```

### 4. Async support

All decorators work with async functions:

```python
@trace_mcp_tool()
async def async_search(query: str) -> list:
    results = await database.search(query)
    return results
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `HEIMDALL_API_KEY` | API key for authentication | Required |
| `HEIMDALL_ENDPOINT` | Heimdall platform URL | `https://api.heimdall.dev` |
| `HEIMDALL_SERVICE_NAME` | Service name for traces | `mcp-server` |
| `HEIMDALL_ENVIRONMENT` | Deployment environment | `development` |
| `HEIMDALL_ENABLED` | Enable/disable tracing | `true` |
| `HEIMDALL_DEBUG` | Enable debug logging | `false` |
| `HEIMDALL_BATCH_SIZE` | Spans per batch | `100` |
| `HEIMDALL_FLUSH_INTERVAL_MS` | Flush interval (ms) | `5000` |

## Advanced Usage

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

