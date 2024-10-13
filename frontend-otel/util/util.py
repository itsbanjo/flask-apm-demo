import logging
import os
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

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_otlp_connection():
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

    # Create namespaced logger
    otlp_logger = logging.getLogger("otlp.test")

    # Create tracer and meter
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    # Define metrics
    metric_name = "otlp_test_counter"
    otlp_test_counter = meter.create_counter(
        name=metric_name,
        description="Counts the number of successful OTLP tests",
        unit="1"
    )

    try:
        # Test span with correlated log
        with tracer.start_as_current_span("test-span") as span:
            span.set_attribute("test.attribute", "test-value")
            otlp_test_counter.add(1)
            
            # Get the trace ID as a hexadecimal string
            trace_id = trace.get_current_span().get_span_context().trace_id
            trace_id_hex = '{:032x}'.format(trace_id)
            
            otlp_logger.info("Test span created", extra={"trace_id": trace_id_hex})

        # Force flush to ensure the span is exported
        trace.get_tracer_provider().force_flush()

        otlp_logger.info("OTLP connection test completed. Check your Elastic APM server for the test data.")
        logger.info(f"Look for the following data in Elastic APM:")
        logger.info(f"1. Service name: 'otlp-test-util'")
        logger.info(f"2. Span name: 'test-span'")
        logger.info(f"3. Metric name: '{metric_name}'")
        logger.info(f"4. Log messages: 'Test span created' and 'OTLP connection test completed'")
        logger.info("If you don't see the data in Elastic APM, check the following:")
        logger.info("1. Verify the OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS are correct")
        logger.info("2. Check Elastic APM server logs for any ingestion errors")
        logger.info("3. Ensure your Elastic APM server is configured to receive OTLP data")
        logger.info("4. Check network connectivity between this client and the Elastic APM server")

    except Exception as e:
        logger.exception(f"An error occurred during the OTLP test: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")

    finally:
        # Shutdown logger provider
        logger_provider.shutdown()

if __name__ == "__main__":
    test_otlp_connection()
