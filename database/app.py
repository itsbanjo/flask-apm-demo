from flask import Flask, request, jsonify
import random
import time
from elasticapm.contrib.flask import ElasticAPM
import os
from datetime import datetime
import elasticapm
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'database'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'CAPTURE_BODY': 'all',
    'CAPTURE_HEADERS': True,
}
apm = ElasticAPM(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@postgres:5432/inventory')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

# Create tables
def init_db():
    Base.metadata.create_all(engine)
    
    # Add some sample data if the table is empty
    session = Session()
    if session.query(Product).count() == 0:
        sample_products = [
            Product(name="Product A", quantity=100, price=19.99),
            Product(name="Product B", quantity=150, price=29.99),
            Product(name="Product C", quantity=200, price=39.99)
        ]
        session.add_all(sample_products)
        session.commit()
    session.close()

# Call init_db() when the app starts
with app.app_context():
    init_db()

def log_with_timestamp(message):
    timestamp = datetime.now().isoformat()
    print(f"{timestamp}: {message}")

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    log_with_timestamp("Received inventory update request")
    
    data = request.json
    if not data:
        return jsonify({'message': 'No JSON data received'}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    if not product_id or quantity is None:
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        quantity = int(quantity)
    except ValueError:
        return jsonify({'message': 'Quantity must be a valid integer'}), 400

    high_latency = data.get('high_latency', False)
    user_region = data.get('user_region', 'Unknown')
    device_type = data.get('device_type', 'Unknown')
    
    elasticapm.set_custom_context({
        'product_id': product_id,
        'quantity': quantity,
        'high_latency': high_latency,
        'user_region': user_region,
        'device_type': device_type
    })
    
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
    elif user_region == 'South America':
        delay = random.uniform(1, 3)
    else:
        delay = random.uniform(0.1, 0.5)
    
    log_with_timestamp(f"Simulating latency. Waiting for {delay:.2f} seconds")
    time.sleep(delay)
    
    session = Session()
    try:
        with elasticapm.capture_span('database_operation', span_type='db'):
            product = session.query(Product).filter_by(id=product_id).first()
            if product:
                product.quantity -= quantity
                session.commit()
                log_with_timestamp("Inventory updated successfully")
                return jsonify({'message': 'Inventory updated successfully', 'new_quantity': product.quantity}), 200
            else:
                log_with_timestamp("Product not found")
                return jsonify({'message': 'Product not found'}), 404
    except Exception as e:
        session.rollback()
        log_with_timestamp(f"Error updating inventory: {str(e)}")
        elasticapm.capture_exception()
        return jsonify({'message': 'Error updating inventory'}), 500
    finally:
        session.close()

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    name = data.get('name')
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0.0))

    session = Session()
    try:
        with elasticapm.capture_span('database_operation', span_type='db'):
            new_product = Product(name=name, quantity=quantity, price=price)
            session.add(new_product)
            session.commit()
        return jsonify({'message': 'Product added successfully', 'product_id': new_product.id}), 201
    except Exception as e:
        session.rollback()
        elasticapm.capture_exception()
        return jsonify({'message': 'Error adding product'}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
