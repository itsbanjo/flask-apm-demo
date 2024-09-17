from flask import Flask, request, jsonify, render_template
import requests
import os
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__)

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'frontend'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
}
apm = ElasticAPM(app)

BACKEND_SERVICE_URL = os.getenv('BACKEND_SERVICE_URL', 'http://localhost:5002')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def place_order():
    user_id = request.form.get('user_id')
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    region = request.form.get('region')
    device_type = request.form.get('device_type')

    headers = {
        'X-User-Region': region,
        'X-Device-Type': device_type
    }

    response = requests.post(
        f"{BACKEND_SERVICE_URL}/process_order",
        json={'user_id': user_id, 'product_id': product_id, 'quantity': quantity},
        headers=headers
    )

    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
