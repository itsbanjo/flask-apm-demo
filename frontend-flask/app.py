from flask import Flask, request, jsonify, render_template
import requests
import os
import logging
from elasticapm.contrib.flask import ElasticAPM
import elasticapm
from elasticapm import Client as ElasticAPMClient

app = Flask(__name__)

logging.basicConfig(filename='/var/log/frontend.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')


# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'frontend-flask'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'CAPTURE_HEADERS': True,
    'CAPTURE_BODY': 'all'
}
apm = ElasticAPM(app)
elastic_apm_client = ElasticAPMClient(app.config['ELASTIC_APM'])

BACKEND_SERVICE_URL = os.getenv('BACKEND_SERVICE_URL', 'http://backend:5002')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def place_order():
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()

    logging.info(f"Received order: {data}")

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    product_name = data.get('product_name')
    quantity = data.get('quantity')
    price = data.get('price')
    region = data.get('region')
    device_type = data.get('device_type')

    high_latency = request.headers.get('X-High-Latency', 'false').lower() == 'true'

    headers = {
        'Content-Type': 'application/json',
        'X-User-Region': region,
        'X-Device-Type': device_type,
        'X-High-Latency': str(high_latency)
    }

    elasticapm.set_custom_context({
        'user_id': user_id,
        'product_id': product_id,
        'product_name': product_name,
        'quantity': quantity,
        'price': price,
        'region': region,
        'device_type': device_type,
        'high_latency': high_latency
    })

    if high_latency:
        elasticapm.label(
            order_type='high_latency',
            frontend_service='flask',
            serviceMetadata='High Latency Enabled'
        )

    try:
        response = requests.post(
            f"{BACKEND_SERVICE_URL}/process_order",
            json={
                'user_id': user_id,
                'product_id': product_id,
                'product_name': product_name,
                'quantity': quantity,
                'price': price 
            },
            headers=headers
        )
        response.raise_for_status()
        app.logger.info(f"Order processed successfully: {response.json()}")
        logging.info(f"Order processed: {response.json()}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error communicating with backend: {str(e)}")
        logging.error(f"Error processing order: {str(e)}")
        elastic_apm_client.capture_exception()
        return jsonify({'message': 'Error processing order'}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
