# Flask APM Demo

This project demonstrates the implementation of Elastic APM (Application Performance Monitoring) in a microservices architecture using Flask. It includes frontend, backend, and database services, along with Locust for load testing.

## Project Structure

```
flask-apm-demo/
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── database/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── locust/
│   ├── Dockerfile
│   ├── locustfile.py
│   └── requirements.txt
└── .env
```

## Services

- Frontend: Handles user requests (Port 5001)
- Backend: Processes business logic (Port 5002)
- Database: Simulates data storage operations (Port 5003)
- Locust: Load testing tool

## Prerequisites

- Docker and Docker Compose
- Elastic APM Server (setup instructions not included in this demo)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/flask-apm-demo.git
   cd flask-apm-demo
   ```

2. Create a `.env` file in the root directory with the following content:
   ```
   ELASTIC_APM_SERVER_URL=http://your-apm-server-url:8200
   ELASTIC_APM_SECRET_TOKEN=your_secret_token_here
   ```

3. Build and start the services:
   ```
   docker-compose up --build -d
   ```

## Usage

1. Access the frontend at `http://localhost:5001`

2. To run a load test with Locust:
   - Open `http://localhost:8089` in your browser
   - Set the number of users and spawn rate
   - Start the test

3. Monitor the performance in your Elastic APM dashboard

## API Endpoints

- Frontend: `POST /order`
- Backend: `POST /process_order`
- Database: `POST /update_inventory`

## Elastic APM Integration

This demo showcases several Elastic APM features:

- Distributed tracing across microservices
- Custom context and labels for detailed transaction information
- Performance monitoring and error tracking
- Latency correlation for identifying performance bottlenecks

Key APM integration points:

- Manual instrumentation in each service
- Propagation of custom headers (X-User-Region, X-Device-Type)
- Simulation of various latency scenarios

## Simulating Scenarios

- High Latency: Activated through the frontend UI
- Region-specific Latency: Simulated for South America in the database service
- Device-specific Errors: 10% error rate for mobile devices in the database service

## Troubleshooting

- Check Docker logs: `docker-compose logs`
- Ensure all services are running: `docker-compose ps`
- Verify APM server connectivity in each service's logs

## Contributing

Contributions to improve the demo are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

[MIT License](https://opensource.org/licenses/MIT)

## Acknowledgments

- Elastic for providing the APM solution
- Flask community for the excellent web framework
- Locust team for the load testing tool
