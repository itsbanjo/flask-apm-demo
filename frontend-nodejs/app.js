const express = require('express');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

// Elastic APM setup
const apm = require('elastic-apm-node').start({
  serviceName: process.env.ELASTIC_APM_SERVICE_NAME || 'frontend-nodejs',
  serverUrl: process.env.ELASTIC_APM_SERVER_URL || 'http://localhost:8200',
  secretToken: process.env.ELASTIC_APM_SECRET_TOKEN,
  captureHeaders: true,
});

const app = express();
const port = process.env.PORT || 5004;
const BACKEND_SERVICE_URL = process.env.BACKEND_SERVICE_URL || 'http://backend:5002';

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/order', async (req, res) => {
  const transaction = apm.startTransaction('place_order', 'request');
  const startTime = Date.now();

  try {
    const { user_id, product_id, quantity, region, device_type, high_latency } = req.body;

    // Set custom context
    transaction.setCustomContext({
      user_id,
      product_id,
      quantity,
      region,
      device_type,
      high_latency
    });

    // Add labels
    transaction.setLabel('order_type', 'standard');
    transaction.setLabel('region', region);
    transaction.setLabel('device_type', device_type);

    const response = await axios.post(`${BACKEND_SERVICE_URL}/process_order`, {
      user_id,
      product_id,
      quantity,
      high_latency
    }, {
      headers: {
        'X-User-Region': region,
        'X-Device-Type': device_type
      }
    });

    const processingTime = (Date.now() - startTime) / 1000; // Convert to seconds

    // Record metrics
    apm.setTransactionName('POST /order');
    apm.setCustomContext({ processingTime });

    res.json({ message: response.data.message, processingTime });
  } catch (error) {
    console.error('Error processing order:', error.message);
    apm.captureError(error);
    res.status(500).json({ message: 'Error processing order' });
  } finally {
    if (transaction) transaction.end();
  }
});

app.listen(port, () => {
  console.log(`Frontend server listening at http://localhost:${port}`);
});
