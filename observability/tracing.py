"""
OpenTelemetry Tracing Configuration
"""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from utils.logger import get_logger

logger = get_logger("tracing")

class TracingService:
    """Service for managing OpenTelemetry tracing"""
    
    def __init__(self):
        self.enabled = False
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer = None
    
    def setup_tracing(self, service_name: str = "scholarship-api"):
        """Setup OpenTelemetry tracing"""
        try:
            # Check if OTLP endpoint is configured
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            
            if not otlp_endpoint:
                logger.info("No OTEL_EXPORTER_OTLP_ENDPOINT configured, using no-op tracer")
                return
            
            # Create resource
            resource = Resource.create({
                "service.name": service_name,
                "service.version": "1.0.0",
                "deployment.environment": os.getenv("ENVIRONMENT", "local")
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=self._get_otlp_headers()
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            self.enabled = True
            
            logger.info(f"OpenTelemetry tracing enabled, exporting to {otlp_endpoint}")
            
        except Exception as e:
            logger.warning(f"Failed to setup tracing: {str(e)}")
            self.enabled = False
    
    def _get_otlp_headers(self) -> dict:
        """Get OTLP headers from environment"""
        headers = {}
        
        # Add auth headers if configured
        auth_header = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
        if auth_header:
            # Parse headers format: "key1=value1,key2=value2"
            for header in auth_header.split(","):
                if "=" in header:
                    key, value = header.strip().split("=", 1)
                    headers[key] = value
        
        return headers
    
    def instrument_app(self, app):
        """Instrument FastAPI app with tracing"""
        if not self.enabled:
            return
            
        try:
            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(app)
            
            # Instrument SQLAlchemy
            SQLAlchemyInstrumentor().instrument()
            
            # Instrument requests
            RequestsInstrumentor().instrument()
            
            logger.info("Application instrumented with OpenTelemetry")
            
        except Exception as e:
            logger.warning(f"Failed to instrument app: {str(e)}")
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        try:
            if not self.enabled:
                return None
                
            span = trace.get_current_span()
            if span and span.is_recording():
                return format(span.get_span_context().trace_id, '032x')
            return None
            
        except Exception:
            return None

# Global tracing service instance
tracing_service = TracingService()