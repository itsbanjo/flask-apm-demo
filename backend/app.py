# backend/app.py

from flask import Flask, request, jsonify
import requests
import os
import random
import time
from elasticapm.contrib.flask import ElasticAPM
from datetime import datetime
import elasticapm

app = Flask(__name__)

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'backend'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'CAPTURE_HEADERS': ['X-User-Region', 'X-Device-Type']  # Explicitly capture these headers
}
apm = ElasticAPM(app)

DATABASE_SERVICE_URL = os.getenv('DATABASE_SERVICE_URL', 'http://database:5003')

def log_with_timestamp(message):
    timestamp = datetime.now().isoformat()
    print(f"{timestamp}: {message}")

@app.route('/process_order', methods=['POST'])
def process_order():
    log_with_timestamp("Received order processing request")
    
    user_id = request.form.get('user_id')
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    high_latency = request.form.get('high_latency') == 'true'
    
    # Capture custom headers
    user_region = request.headers.get('X-User-Region', 'Unknown')
    device_type = request.headers.get('X-Device-Type', 'Unknown')
    
    # Add custom context to the current transaction
    elasticapm.set_custom_context({
        'user_id': user_id,
        'product_id': product_id,
        'quantity': quantity,
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
    
    log_with_timestamp(f"Processing order - High Latency: {high_latency}, Region: {user_region}, Device: {device_type}")
    
    # Simulate high latency if flag is set
    if high_latency:
        delay = random.uniform(3, 5)
        log_with_timestamp(f"Simulating high latency. Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    else:
        delay = random.uniform(0.1, 0.5)
        log_with_timestamp(f"Normal processing. Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    
    # Forward request to database service
    try:
        log_with_timestamp("Sending request to database service")
        response = requests.post(
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
        response.raise_for_status()
        log_with_timestamp("Received response from database service")
    except requests.exceptions.RequestException as e:
        log_with_timestamp(f"Error communicating with database service: {str(e)}")
        elasticapm.set_custom_context({'error_details': str(e)})
        return jsonify({'message': 'Error processing order'}), 500
    
    log_with_timestamp("Order processed successfully")
    return jsonify({'message': 'Order processed successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
