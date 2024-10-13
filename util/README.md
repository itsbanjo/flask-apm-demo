# OTLP Test Utility

This utility is designed to test the connection and data transmission to an OpenTelemetry (OTLP) compatible backend, such as Elastic APM. It sends traces, metrics, and logs using the OTLP exporter.

## Prerequisites

- Docker

## Configuration

You need to set the following environment variables when running the utility:

- `OTEL_EXPORTER_OTLP_ENDPOINT`: The endpoint of your OTLP receiver (e.g., `http://localhost:8200`)
- `OTEL_EXPORTER_OTLP_HEADERS`: Headers required for authentication (e.g., `Authorization=Bearer your_token_here`)

## Usage

To run the utility using Docker:

```bash
docker run --rm \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=<CHANGE ME> \
  -e OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer%20<CHANGE_ME>" \
  banjodocker/otlp-test-util
```

Replace `<CHANGE ME>` with your OTLP endpoint URL and `<CHANGE_ME>` with your actual bearer token.

This will:
1. Create a test span
2. Increment a test counter metric
3. Send log messages
4. Output information about the test data sent

Check your Elastic APM server (or other OTLP-compatible backend) for the following data:
1. Service name: 'otlp-test-util'
2. Span name: 'test-span'
3. Metric name: 'otlp_test_counter'
4. Log messages: 'Test span created' and 'OTLP connection test completed'

## Troubleshooting

If you don't see the data in your backend:
1. Verify the `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` are correct
2. Check your backend server logs for any ingestion errors
3. Ensure your backend is configured to receive OTLP data
4. Check network connectivity between this client and the backend server

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
