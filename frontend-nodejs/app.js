const express = require('express');
const axios = require('axios');
const path = require('path');
const apm = require('elastic-apm-node').start({
  serviceName: 'frontend-nodejs',
  serverUrl: process.env.ELASTIC_APM_SERVER_URL || 'http://localhost:8200',
  secretToken: process.env.ELASTIC_APM_SECRET_TOKEN || '',
  captureHeaders: true,
  captureBody: 'errors'
});

const app = express();
const port = 5004;

app.use(express.static('public'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const BACKEND_SERVICE_URL = process.env.BACKEND_SERVICE_URL || 'http://backend:5002';

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/order', async (req, res) => {
  console.log('Order route hit');
  const transaction = apm.startTransaction('POST /order', 'request');
  
  try {
    const { user_id, product_id, product_name, quantity, price, region, device_type } = req.body;
    
    console.log('Order details:', { user_id, product_id, product_name, quantity, price, region, device_type });

    apm.setCustomContext({
      user_id,
      product_id,
      product_name,
      quantity,
      price,
      region,
      device_type
    });
    apm.setLabel('order_type', 'standard');
    apm.setLabel('frontend_service', 'nodejs');

    const headers = {
      'Content-Type': 'application/json',
      'X-User-Region': region,
      'X-Device-Type': device_type
    };

    console.log('Sending request to backend:', `${BACKEND_SERVICE_URL}/process_order`);
    try {
      const response = await axios.post(`${BACKEND_SERVICE_URL}/process_order`, {
        user_id,
        product_id,
        product_name,
        quantity,
        price
      }, { headers });

      console.log('Backend response:', response.data);
      res.json(response.data);
    } catch (error) {
      console.error('Error from backend:', error.response ? error.response.data : error.message);
      console.error('Error status:', error.response ? error.response.status : 'Unknown');
      console.error('Error headers:', error.response ? error.response.headers : 'Unknown');
      apm.captureError(error);
      res.status(error.response ? error.response.status : 500).json({ message: 'Error processing order' });
    }
  } catch (error) {
    console.error('Error in place_order:', error.message);
    apm.captureError(error);
    res.status(500).json({ message: 'Internal server error' });
  } finally {
    if (transaction) transaction.end();
  }
});

app.listen(port, () => {
  console.log(`Node.js frontend listening at http://localhost:${port}`);
});
