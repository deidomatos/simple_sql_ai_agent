import os
import logging
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def setup_tracing():
    """Set up OpenTelemetry tracing"""
    enable_tracing = os.getenv("ENABLE_TRACING", "false").lower() == "true"
    
    if not enable_tracing:
        logger.info("Tracing is disabled")
        return
    
    # Create a resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: "sql-agent"
    })
    
    # Create a tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Configure the exporter
    exporter_type = os.getenv("TRACING_EXPORTER", "console").lower()
    
    if exporter_type == "otlp":
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP tracing enabled, sending to {otlp_endpoint}")
    else:  # Default to console
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console tracing enabled")
    
    return tracer_provider

def get_tracer(name):
    """Get a tracer for the given name"""
    return trace.get_tracer(name)