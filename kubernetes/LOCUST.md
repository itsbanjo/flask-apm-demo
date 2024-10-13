# Locust Load Testing in Kubernetes

## TLDR

```bash
# Apply Locust configuration
kubectl apply -f locust-config.yaml

# Access Locust web interface
# Replace <ingress-address> with your actual ingress address
open http://<ingress-address>/locust/

# View Locust logs
kubectl logs -l app=locust

# Delete Locust deployment
kubectl delete -f locust-config.yaml
```

---

## Overview

This README provides instructions for deploying and using Locust, a modern load testing tool, in a Kubernetes environment. Locust is used to simulate user behavior and test the performance of your application under various load conditions.

## Prerequisites

- A running Kubernetes cluster
- `kubectl` configured to communicate with your cluster
- Basic understanding of Kubernetes concepts
- Familiarity with Locust and load testing principles

## Deployment

### 1. Apply the Locust Configuration

Apply the Locust configuration to your Kubernetes cluster:

```bash
kubectl apply -f locust-config.yaml
```

This will create:
- A Locust deployment
- A Kubernetes service for Locust
- An Ingress resource to expose Locust
- A ConfigMap containing the Locust tasks

### 2. Verify Deployment

Check if the Locust pod is running:

```bash
kubectl get pods -l app=locust
```

## Accessing Locust

Access the Locust web interface through your ingress:

```
http://<your-ingress-address>/locust/
```

Replace `<your-ingress-address>` with the actual address of your ingress.

## Running Load Tests

1. Open the Locust web interface.
2. Enter the number of users to simulate.
3. Set the spawn rate (users started/second).
4. Start the test and monitor the results.

## Customizing Locust Tasks

The Locust tasks are defined in the ConfigMap section of `locust-config.yaml`. To modify the tasks:

1. Edit the `locustfile.py` content in the ConfigMap.
2. Apply the changes:
   ```bash
   kubectl apply -f locust-config.yaml
   ```
3. Restart the Locust pod to pick up the new configuration:
   ```bash
   kubectl rollout restart deployment locust
   ```

## Viewing Logs

To view Locust logs:

```bash
kubectl logs -l app=locust
```

## Cleanup

To remove Locust from your cluster:

```bash
kubectl delete -f locust-config.yaml
```

## Troubleshooting

If you encounter issues:

1. Check Locust pod status:
   ```bash
   kubectl describe pod -l app=locust
   ```
2. Verify Ingress configuration:
   ```bash
   kubectl describe ingress locust-ingress
   ```
3. Ensure your Ingress controller is properly configured.

## Additional Resources

- [Locust Documentation](https://docs.locust.io/en/stable/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
