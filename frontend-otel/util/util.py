import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_otlp_connection():
    # Set up resource
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: "otlp-test-util",
        ResourceAttributes.SERVICE_VERSION: "1.0",
    })

    # Set up tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Create OTLP exporter
    # This will automatically use OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS
    otlp_exporter = OTLPSpanExporter()
    
    # Log the exporter configuration (for debugging)
    logger.info(f"OTLP Exporter created. It will use the following environment variables:")
    logger.info("OTEL_EXPORTER_OTLP_ENDPOINT for the APM server URL")
    logger.info("OTEL_EXPORTER_OTLP_HEADERS for the authorization token")

    # Set up span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Metrics configuration
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    # Logs configuration
    otlp_log_exporter = OTLPLogExporter()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    # Create tracer
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    # Define metrics
    otlp_test_counter = meter.create_counter(
    name="otlp_test_counter",
    description="Counts the number of successfull otlp test",
    unit="1"
    )

    try:
        # Test span
        with tracer.start_as_current_span("test-span") as span:
            span.set_attribute("test.attribute", "test-value")
            otlp_test_counter.add(1)
            logger.info("Test span created")

        # Force flush to ensure the span is exported
        trace.get_tracer_provider().force_flush()

        logger.info("OTLP connection test completed. Check your Elastic APM server for the test data.")

    except Exception as e:
        logger.exception(f"An error occurred during the OTLP test: {str(e)}")

if __name__ == "__main__":
    test_otlp_connection()
