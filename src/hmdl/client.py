"""Heimdall client for OpenTelemetry-based observability."""

from __future__ import annotations

import atexit
import logging
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from hmdl.config import HeimdallConfig
from hmdl.types import HeimdallAttributes

logger = logging.getLogger(__name__)


class HeimdallClient:
    """Client for sending observability data to Heimdall platform.
    
    This client sets up OpenTelemetry tracing and provides methods for
    creating spans and recording MCP operations.
    
    Example:
        >>> from hmdl import HeimdallClient
        >>> client = HeimdallClient(api_key="your-api-key")
        >>> with client.start_span("my-operation") as span:
        ...     # Your code here
        ...     span.set_attribute("custom.attribute", "value")
    """
    
    _instance: Optional["HeimdallClient"] = None
    _initialized: bool = False
    
    def __new__(cls, *args: Any, **kwargs: Any) -> "HeimdallClient":
        """Singleton pattern to ensure only one client instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        config: Optional[HeimdallConfig] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        service_name: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        """Initialize the Heimdall client.
        
        Args:
            config: Full configuration object. If provided, other args are ignored.
            api_key: API key for Heimdall platform.
            endpoint: Heimdall platform endpoint URL.
            service_name: Name of the service being instrumented.
            environment: Deployment environment.
        """
        if self._initialized:
            return
            
        # Build config from arguments or use provided config
        if config is not None:
            self.config = config
        else:
            self.config = HeimdallConfig(
                api_key=api_key or HeimdallConfig().api_key,
                endpoint=endpoint or HeimdallConfig().endpoint,
                service_name=service_name or HeimdallConfig().service_name,
                environment=environment or HeimdallConfig().environment,
            )
        
        self._tracer: Optional[trace.Tracer] = None
        self._provider: Optional[TracerProvider] = None
        
        if self.config.enabled:
            self._setup_tracing()
        
        self._initialized = True
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    def _setup_tracing(self) -> None:
        """Set up OpenTelemetry tracing."""
        if self.config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: self.config.service_name,
            HeimdallAttributes.HEIMDALL_ENVIRONMENT: self.config.environment,
        })
        
        # Create tracer provider
        self._provider = TracerProvider(resource=resource)
        
        # Set up OTLP exporter
        otlp_endpoint = f"{self.config.endpoint}/v1/traces"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers,
        )
        
        # Add batch processor for efficient span export
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=self.config.max_queue_size,
            max_export_batch_size=self.config.batch_size,
            schedule_delay_millis=self.config.flush_interval_ms,
        )
        self._provider.add_span_processor(processor)
        
        # Set as global tracer provider
        trace.set_tracer_provider(self._provider)
        
        # Get tracer
        self._tracer = trace.get_tracer("hmdl", "0.1.0")
        
        logger.debug(f"Heimdall tracing initialized for service: {self.config.service_name}")

    @property
    def tracer(self) -> trace.Tracer:
        """Get the OpenTelemetry tracer."""
        if self._tracer is None:
            # Return a no-op tracer if not initialized
            return trace.get_tracer("hmdl-noop")
        return self._tracer

    def start_span(
        self,
        name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> trace.Span:
        """Start a new span.

        Args:
            name: Name of the span.
            kind: Kind of span (INTERNAL, CLIENT, SERVER, etc.).
            attributes: Initial attributes for the span.

        Returns:
            The created span as a context manager.
        """
        return self.tracer.start_as_current_span(
            name=name,
            kind=kind,
            attributes=attributes,
        )

    def get_current_span(self) -> trace.Span:
        """Get the current active span."""
        return trace.get_current_span()

    def flush(self) -> None:
        """Flush all pending spans."""
        if self._provider is not None:
            self._provider.force_flush()

    def shutdown(self) -> None:
        """Shutdown the client and flush remaining spans."""
        if self._provider is not None:
            self._provider.shutdown()
            logger.debug("Heimdall client shutdown complete")

    @classmethod
    def get_instance(cls) -> Optional["HeimdallClient"]:
        """Get the singleton client instance."""
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        if cls._instance is not None:
            cls._instance.shutdown()
        cls._instance = None
        cls._initialized = False

