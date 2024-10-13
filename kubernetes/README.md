# Microservices Order Processing System

## TLDR: Quick Deployment

```bash
# Create a secrets file
cat <<EOF > elastic-apm-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: elastic-apm-secret
type: Opaque
stringData:
  server-url: "https://your-apm-server-url:8200"
  secret-token: "your_secret_token_here"
EOF

# Apply secrets
kubectl apply -f elastic-apm-secrets.yaml

# Deploy the application
kubectl apply -f microservices-deployment.yaml

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress
```

Replace `https://your-apm-server-url:8200` and `your_secret_token_here` with your actual Elastic APM server URL and secret token.

---

## Architecture

The system consists of the following components:

1. Frontend Service (with Flask, Node.js, and OpenTelemetry implementations)
2. Backend Service
3. Database Service
4. PostgreSQL Database

## Prerequisites

- Kubernetes cluster
- `kubectl` configured to communicate with your cluster
- Elastic APM server (for monitoring)

## Deployment

### 1. Prepare the Environment

Create a Kubernetes secret for Elastic APM:

```bash
kubectl create secret generic elastic-apm-secret \
  --from-literal=server-url=<your-apm-server-url> \
  --from-literal=secret-token=<your-secret-token>
```

Replace `<your-apm-server-url>` and `<your-secret-token>` with your actual Elastic APM server URL and secret token.

### 2. Deploy the Application

Apply the Kubernetes configuration:

```bash
kubectl apply -f microservices-deployment.yaml
```

This will create all necessary deployments, services, and the ingress.

## Components

### Frontend Service

- Implemented in Flask, Node.js, and with OpenTelemetry
- All implementations are deployed under a single service named `frontend`
- Accessible via the ingress on the root path (`/`)

### Backend Service

- Handles business logic
- Communicates with the database service

### Database Service

- Interfaces with PostgreSQL
- Handles data persistence

### PostgreSQL

- Stores application data

## Ingress

The ingress is configured to route all traffic to the frontend service, which load balances across all frontend implementations.

## Monitoring

All services are configured to send telemetry data to Elastic APM. The frontend implementations all report under the service name "frontend" for unified monitoring.

## Customization

- To adjust the number of replicas, modify the `replicas` field in the respective deployment specifications.
- To change resource allocations, add `resources` specifications to the container definitions.
- For production use, consider setting up persistent volumes for the PostgreSQL database.

## Troubleshooting

1. Check the status of the pods:
   ```
   kubectl get pods
   ```

2. For detailed information about a pod:
   ```
   kubectl describe pod <pod-name>
   ```

3. To view logs of a specific container:
   ```
   kubectl logs <pod-name> -c <container-name>
   ```

## Security Notes

- The PostgreSQL credentials are currently set in plain text in the deployment file. For production use, consider using Kubernetes secrets for database credentials.
- Ensure that your Elastic APM server is properly secured and that the secret token is kept confidential.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
