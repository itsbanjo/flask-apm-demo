#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to make a request and check the response
make_request() {
    local endpoint=$1
    local method=$2
    local data=$3
    local expected_status=$4

    echo -e "\nTesting ${method} ${endpoint}"
    response=$(curl -s -X ${method} -H "Content-Type: application/json" -d "${data}" -w "\n%{http_code}" ${endpoint})
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}Success: Status $status${NC}"
    else
        echo -e "${RED}Failure: Expected status $expected_status, got $status${NC}"
    fi
    echo "Response body:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
}

# Test Flask Frontend
echo "Testing Flask Frontend (http://localhost:5001)"
make_request "http://localhost:5001/order" "POST" '{"user_id": "user123", "product_id": "1", "quantity": "5", "region": "North America", "device_type": "Desktop"}' 200
make_request "http://localhost:5001/order" "POST" '{"user_id": "user456", "product_name": "New Product", "quantity": "3", "price": "29.99", "region": "Europe", "device_type": "Mobile"}' 200

# Test Node.js Frontend
echo "Testing Node.js Frontend (http://localhost:5004)"
make_request "http://localhost:5004/order" "POST" '{"user_id": "user789", "product_id": "2", "quantity": "2", "region": "Asia", "device_type": "Tablet"}' 200
make_request "http://localhost:5004/order" "POST" '{"user_id": "user101", "product_name": "Another New Product", "quantity": "1", "price": "39.99", "region": "South America", "device_type": "Desktop"}' 200

# Test Backend directly (if accessible)
echo "Testing Backend directly (http://localhost:5002)"
make_request "http://localhost:5002/process_order" "POST" '{"user_id": "user202", "product_id": "3", "quantity": "4"}' 200
make_request "http://localhost:5002/process_order" "POST" '{"user_id": "user303", "product_name": "Direct New Product", "quantity": "2", "price": "49.99"}' 200

# Test Database service directly (if accessible)
echo "Testing Database service directly (http://localhost:5003)"
make_request "http://localhost:5003/update_inventory" "POST" '{"product_id": "1", "quantity": "10"}' 200
make_request "http://localhost:5003/add_product" "POST" '{"name": "Directly Added Product", "quantity": "100", "price": "59.99"}' 201

echo -e "\nAll tests completed."
