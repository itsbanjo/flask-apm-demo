import logging
import os
import time
from opentelemetry import trace, metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry._logs import set_logger_provider
from prometheus_client import start_http_server, Summary, Counter

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus metrics
prom_summary = Summary('otlp_test_summary', 'Summary of OTLP test durations', ['operation'])
prom_counter = Counter('otlp_test_counter', 'Counts the number of successful OTLP tests')

def setup_opentelemetry():
    # Check and log environment variables
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    headers = os.getenv('OTEL_EXPORTER_OTLP_HEADERS')
    logger.info(f"OTEL_EXPORTER_OTLP_ENDPOINT: {endpoint}")
    logger.info(f"OTEL_EXPORTER_OTLP_HEADERS: {headers}")

    if not endpoint or not headers:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT or OTEL_EXPORTER_OTLP_HEADERS not set!")

    # Set up resource
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: "otlp-test-util",
        ResourceAttributes.SERVICE_VERSION: "1.0",
    })

    # Set up tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Create OTLP exporters with explicit configuration
    otlp_span_exporter = OTLPSpanExporter(
        endpoint=endpoint,
        headers=headers,
        timeout=30  # Increased timeout for debugging
    )
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=endpoint,
        headers=headers,
        timeout=30
    )
    otlp_log_exporter = OTLPLogExporter(
        endpoint=endpoint,
        headers=headers,
        timeout=30
    )
    
    # Set up span processor
    span_processor = BatchSpanProcessor(otlp_span_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Metrics configuration
    metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    # Logs configuration
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    # Create logging handler
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)

    return trace.get_tracer(__name__), metrics.get_meter(__name__)

def run_test(tracer, meter):
    otlp_logger = logging.getLogger("otlp.test")

    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("test.attribute", "test-value")
        prom_counter.inc()
        
        # Simulate some work and record its duration
        start_time = time.time()
        time.sleep(0.1)  # Simulate 100ms of work
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Record the duration in the Prometheus summary
        prom_summary.labels(operation="test-span").observe(duration)
        
        # Get the trace ID as a hexadecimal string
        trace_id = trace.get_current_span().get_span_context().trace_id
        trace_id_hex = '{:032x}'.format(trace_id)
        
        otlp_logger.info("Test span created", extra={"trace_id": trace_id_hex})

    logger.info("OTLP test completed. Metrics are available for Prometheus to scrape.")

def main():
    # Start up the server to expose the metrics.
    start_http_server(8000)
    logger.info("Prometheus metrics server started on port 8000")

    tracer, meter = setup_opentelemetry()

    # Run the test in a loop
    while True:
        run_test(tracer, meter)
        time.sleep(10)  # Wait for 10 seconds before running the next test

if __name__ == "__main__":
    main()
