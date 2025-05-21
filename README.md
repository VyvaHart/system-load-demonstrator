# System Load Demonstrator

A Flask web application to generate and visualize configurable system load (CPU, Memory, I/O) deployed to Kubernetes (Minikube) and monitored with Prometheus & Grafana.

## Features

*   **Configurable Load Generation:**
    *   Modes: CPU Heavy, Memory Heavy, I/O Heavy, Balanced.
    *   Adjustable iterations and data sizes.
    *   CPU Algorithms: Fibonacci, Prime Factorization, Hashing.
    *   Optional override flags for forcing specific load types.
*   **Web UI:** Simple HTML form to trigger load scenarios.
*   **Prometheus Metrics:** Exposes application and process metrics via `/metrics`.
*   **Containerized & Kubernetes Ready:** Dockerfile and Kubernetes manifests for Minikube.
*   **CI/CD:** GitHub Actions for building and pushing images to GHCR.

## Tech Stack

*   **Application:** Python 3.11, Flask, Gunicorn
*   **Metrics Library:** `prometheus_flask_exporter`
*   **Containerization:** Docker
*   **Orchestration:** Kubernetes (Minikube)
*   **CI/CD:** GitHub Actions, GitHub Container Registry (GHCR)
*   **Monitoring:** Prometheus (via `kube-prometheus-stack`)
*   **Visualization:** Grafana (via `kube-prometheus-stack`)

## Project Setup & Run

**Prerequisites:**
*   Git
*   Docker Desktop (or Docker Engine)
*   Minikube (started, `minikube start`)
*   `kubectl` (configured for Minikube)
*   Helm

**1. Clone Repository:**
```bash
git clone https://github.com/VyvaHart/system-load-demonstrator.git
cd system-load-demonstrator
git checkout dev # Or main
```

**2. ImagePullSecret (If GHCR Package is Private):**
```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GHCR_PAT \
  --namespace=default
```
**3. Deploy Monitoring Stack (Prometheus & Grafana):**
This uses the kube-prometheus-stack Helm chart
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace prometheus \
  --create-namespace \
  --wait
```
**4. Deploy the Load Shifter Application:**
Choose to deploy the dev or main version (manifests are in k8s/)
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/servicemonitor.yaml
```
**5. Access the Application:**
```bash
# This will open the application UI in your browser. Use the form to generate load
minikube service load-shifter-service --namespace=default
```

**6. Access Monitoring UIs:**
* Prometheus:
```bash
# Find the Prometheus server service (prometheus-operated in my case)
# kubectl get svc -n prometheus
kubectl port-forward svc/prometheus-operated -n prometheus 9090:9090
```
Open http://localhost:9090. Check [Status -> Target health] to ensure your app is UP
* Grafana:
```bash
# Get Grafana admin password
kubectl get secret prometheus-grafana -n prometheus -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
# Access Grafana service
minikube service prometheus-grafana -n prometheus
```

This setup provides a great hands-on learning experience. Have fun exploring!
