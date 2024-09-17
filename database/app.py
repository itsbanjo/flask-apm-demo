# database/app.py

from flask import Flask, request, jsonify
import random
import time
from elasticapm.contrib.flask import ElasticAPM
import os
from datetime import datetime
import elasticapm

app = Flask(__name__)

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'database'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'CAPTURE_HEADERS': ['X-User-Region', 'X-Device-Type']  # Explicitly capture these headers
}
apm = ElasticAPM(app)

def log_with_timestamp(message):
    timestamp = datetime.now().isoformat()
    print(f"{timestamp}: {message}")

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    log_with_timestamp("Received inventory update request")
    
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    high_latency = data.get('high_latency', False)
    user_region = data.get('user_region', 'Unknown')
    device_type = data.get('device_type', 'Unknown')
    
    # Add custom context to the current transaction
    elasticapm.set_custom_context({
        'product_id': product_id,
        'quantity': quantity,
        'high_latency': high_latency,
        'user_region': user_region,
        'device_type': device_type
    })
    
    # Add labels to the current transaction
    elasticapm.label(
        inventory_action='update',
        product_category='standard',
        user_region=user_region,
        device_type=device_type
    )
    
    log_with_timestamp(f"Updating inventory - High Latency: {high_latency}, Region: {user_region}, Device: {device_type}")
    
    # Simulate database latency
    if high_latency:
        delay = random.uniform(2, 4)
        log_with_timestamp(f"Simulating high latency. Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    else:
        if user_region == 'South America':
            delay = random.uniform(1, 3)
            log_with_timestamp(f"High latency for South America. Waiting for {delay:.2f} seconds")
            time.sleep(delay)
        else:
            delay = random.uniform(0.1, 0.5)
            log_with_timestamp(f"Normal latency. Waiting for {delay:.2f} seconds")
            time.sleep(delay)
    
    # Simulate occasional errors for mobile devices
    if device_type == 'Mobile' and random.random() < 0.1:  # 10% error rate for mobile
        log_with_timestamp("Simulated error for mobile device")
        elasticapm.set_custom_context({'error_reason': 'Mobile device random error'})
        return jsonify({'message': 'Database error'}), 500
    
    log_with_timestamp("Inventory updated successfully")
    return jsonify({'message': 'Inventory updated successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
