# backend/app.py

from flask import Flask, request, jsonify
import requests
import logging
import os
import random
import time
from elasticapm.contrib.flask import ElasticAPM
import elasticapm

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename='/var/log/backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'backend'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'CAPTURE_HEADERS': ['X-User-Region', 'X-Device-Type']
}
apm = ElasticAPM(app)

DATABASE_SERVICE_URL = os.getenv('DATABASE_SERVICE_URL', 'http://database:5003')

@app.route('/process_order', methods=['POST'])
def process_order():
    logger.info("Received order processing request")
    
    data = request.json
    if not data:
        logger.error("No JSON data received")
        return jsonify({'message': 'No JSON data received'}), 400

    logger.info(f"Processing order: {data}")

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    product_name = data.get('product_name')
    quantity = data.get('quantity')
    price = data.get('price')
    
    if not all([user_id, quantity]) or (not product_id and not product_name):
        logger.error(f"Missing required fields. Data received: {data}")
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        quantity = int(quantity)
        if price:
            price = float(price)
    except ValueError:
        logger.error(f"Invalid quantity or price. Quantity: {quantity}, Price: {price}")
        return jsonify({'message': 'Invalid quantity or price'}), 400

    high_latency = request.headers.get('X-High-Latency', 'false').lower() == 'true'
    user_region = request.headers.get('X-User-Region', 'Unknown')
    device_type = request.headers.get('X-Device-Type', 'Unknown')
    
    # Add custom context to the current transaction
    elasticapm.set_custom_context({
        'user_id': user_id,
        'product_id': product_id,
        'product_name': product_name,
        'quantity': quantity,
        'price': price,
        'high_latency': high_latency,
        'user_region': user_region,
        'device_type': device_type
    })
    
    # Add labels to the current transaction
    elasticapm.label(
        order_type='standard',
        processing_priority='normal',
        user_region=user_region,
        device_type=device_type
    )
    
    logger.info(f"Processing order - High Latency: {high_latency}, Region: {user_region}, Device: {device_type}")
    
    # Simulate high latency if flag is set
    if high_latency:
        delay = random.uniform(5, 7)
        logger.info(f"Simulating high latency. Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    else:
        delay = random.uniform(0.1, 0.5)
        logger.info(f"Normal processing. Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    
    # Check if product exists or needs to be added
    try:
        if not product_id:
            # Add new product
            logger.info(f"Adding new product: {product_name}")
            add_product_response = requests.post(
                f"{DATABASE_SERVICE_URL}/add_product",
                json={
                    'name': product_name,
                    'quantity': quantity,
                    'price': price
                },
                headers={
                    'X-User-Region': user_region,
                    'X-Device-Type': device_type
                },
                timeout=10
            )
            add_product_response.raise_for_status()
            product_data = add_product_response.json()
            product_id = product_data.get('product_id')
            logger.info(f"New product added with ID: {product_id}")

        # Update inventory
        logger.info(f"Updating inventory for product ID: {product_id}")
        update_inventory_response = requests.post(
            f"{DATABASE_SERVICE_URL}/update_inventory",
            json={
                'product_id': product_id,
                'quantity': quantity,
                'high_latency': high_latency,
                'user_region': user_region,
                'device_type': device_type
            },
            headers={
                'X-User-Region': user_region,
                'X-Device-Type': device_type
            },
            timeout=10
        )
        update_inventory_response.raise_for_status()
        logger.info("Inventory updated successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with database service: {str(e)}")
        elasticapm.set_custom_context({'error_details': str(e)})
        return jsonify({'message': 'Error processing order'}), 500
    
    logger.info("Order processed successfully")
    return jsonify({'message': 'Order processed successfully', 'product_id': product_id}), 200

if __name__ == '__main__':
    logger.info("Starting backend server")
    app.run(host='0.0.0.0', port=5002)
