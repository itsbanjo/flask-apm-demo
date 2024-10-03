from flask import Flask, request, jsonify, render_template
import requests
import logging
import time
import random
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure OpenTelemetry
resource = Resource(attributes={
    ResourceAttributes.SERVICE_NAME: "frontend-otel",
    ResourceAttributes.SERVICE_VERSION: "1.0",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production"
})

# Trace configuration
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_span_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_span_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Metrics configuration
metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

# Logs configuration
otlp_log_exporter = OTLPLogExporter()
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Instrument requests library
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Define metrics
order_counter = meter.create_counter(
    name="order_counter",
    description="Counts the number of orders",
    unit="1"
)

order_value_recorder = meter.create_histogram(
    name="order_value",
    description="Records the value of orders",
    unit="$"
)

request_duration = meter.create_histogram(
    name="request_duration",
    description="Duration of requests",
    unit="ms"
)

active_users = meter.create_up_down_counter(
    name="active_users",
    description="Number of active users",
    unit="1"
)

BACKEND_SERVICE_URL = "http://backend:5002"

@app.route('/')
def index():
    logger.info("Accessed home page")
    active_users.add(1)
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def place_order():
    start_time = time.time()
    with tracer.start_as_current_span("place_order") as span:
        transaction_id = str(int(time.time() * 1000))
        logger.info(f"Starting transaction {transaction_id}")
        
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()

        logger.info(f"Received order for transaction {transaction_id}: {data}")

        user_id = data.get('user_id')
        product_id = data.get('product_id')
        product_name = data.get('product_name', '')
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0))
        region = data.get('region')
        device_type = data.get('device_type')

        high_latency = request.headers.get('X-High-Latency', 'false').lower() == 'true'

        headers = {
            'Content-Type': 'application/json',
            'X-User-Region': region,
            'X-Device-Type': device_type,
            'X-High-Latency': str(high_latency)
        }

        span.set_attribute("transaction_id", transaction_id)
        span.set_attribute("user_id", user_id)
        span.set_attribute("product_id", product_id)
        span.set_attribute("product_name", product_name)
        span.set_attribute("quantity", quantity)
        span.set_attribute("price", price)
        span.set_attribute("region", region)
        span.set_attribute("device_type", device_type)
        span.set_attribute("high_latency", high_latency)

        if high_latency:
            span.set_attribute("order_type", "high_latency")
            span.set_attribute("frontend_service", "flask")
            span.set_attribute("serviceMetadata", "High Latency Enabled")
            time.sleep(random.uniform(1, 3))  # Simulate high latency

        # Record metrics
        order_counter.add(1, {"region": region, "device_type": device_type})
        order_value_recorder.record(price * quantity, {"region": region, "device_type": device_type})

        try:
            logger.info(f"Sending request to backend for transaction {transaction_id}")
            response = requests.post(
                f"{BACKEND_SERVICE_URL}/process_order",
                json={
                    'transaction_id': transaction_id,
                    'user_id': user_id,
                    'product_id': product_id,
                    'product_name': product_name,
                    'quantity': quantity,
                    'price': price 
                },
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Order processed successfully for transaction {transaction_id}: {response.json()}")
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with backend for transaction {transaction_id}: {str(e)}")
            span.record_exception(e)
            return jsonify({'message': 'Error processing order'}), 500
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            request_duration.record(duration, {"endpoint": "/order"})
            logger.info(f"Completed transaction {transaction_id} in {duration:.2f}ms")

@app.route('/health')
def health_check():
    logger.info("Health check requested")
    return jsonify({'status': 'healthy'}), 200

@app.route('/simulate_error')
def simulate_error():
    logger.error("Simulated error occurred")
    raise Exception("This is a simulated error")

@app.route('/simulate_slow_request')
def simulate_slow_request():
    with tracer.start_as_current_span("slow_request") as span:
        span.set_attribute("slow_request", True)
        logger.info("Starting slow request simulation")
        time.sleep(5)  # Simulate a slow operation
        logger.info("Completed slow request simulation")
    return "Slow request completed", 200

@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("An unhandled exception occurred")
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    logger.info("Starting Flask application on port 5005")
    app.run(host='0.0.0.0', port=5005)
