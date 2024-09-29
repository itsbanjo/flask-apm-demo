const express = require('express');
const path = require('path');
const axios = require('axios');
const winston = require('winston');
require('dotenv').config();

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: '/var/log/frontend.log' })
  ]
});

// Elastic APM setup
const apm = require('elastic-apm-node').start({
  serviceName: process.env.ELASTIC_APM_SERVICE_NAME || 'frontend-nodejs',
  serverUrl: process.env.ELASTIC_APM_SERVER_URL || 'http://localhost:8200',
  secretToken: process.env.ELASTIC_APM_SECRET_TOKEN,
  environment: process.env.NODE_ENV || 'development',
  captureHeaders: true,
  captureBody: 'all',
  distributedTracingOrigins: [process.env.BACKEND_SERVICE_URL || 'http://backend:5002']
});

const app = express();
const port = process.env.PORT || 5004;
const BACKEND_SERVICE_URL = process.env.BACKEND_SERVICE_URL || 'http://backend:5002';

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.post('/order', async (req, res) => {
  const startTime = Date.now();
  logger.info(`Received order: ${JSON.stringify(req.body)}`);

  const { user_id, product_id, product_name, quantity, price, region, device_type } = req.body;
  const high_latency = req.headers['x-high-latency'] === 'true';

  const transaction = apm.startTransaction('POST /order', 'request');

  try {
    // Set custom context
    apm.setCustomContext({
      user_id,
      product_id,
      product_name,
      quantity,
      price,
      region,
      device_type,
      high_latency
    });

    // Conditional labeling
    if (high_latency) {
      apm.setLabel('order_type', 'high_latency');
      apm.setLabel('frontend_service', 'nodejs');
      apm.setLabel('serviceMetadata', 'High Latency Enabled');
    }
    
    // Create a custom span for the backend request
    const span = transaction.startSpan('POST backend:5002/process_order', 'external.http');

    // Get the trace context from the current transaction
    const traceContext = transaction.traceparent;

    const response = await axios.post(`${BACKEND_SERVICE_URL}/process_order`, {
      user_id,
      product_id,
      product_name,
      quantity,
      price
    }, {
      headers: {
        'X-User-Region': region,
        'X-Device-Type': device_type,
        'X-High-Latency': high_latency.toString(),
        'elastic-apm-traceparent': traceContext // Add the trace context
      }
    });

    if (span) span.end();

    const processingTime = (Date.now() - startTime) / 1000;
    logger.info(`Order processed: ${JSON.stringify(response.data)}`);
    logger.info(`Processing time: ${processingTime} seconds`);

    transaction.result = 'success';
    res.json({ ...response.data, processingTime });
  } catch (error) {
    logger.error(`Error processing order: ${error.message}`);
    transaction.result = 'error';
    apm.captureError(error);
    res.status(500).json({ message: 'Error processing order' });
  } finally {
    if (transaction) transaction.end();
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  logger.info(`Frontend server listening at http://localhost:${port}`);
});
