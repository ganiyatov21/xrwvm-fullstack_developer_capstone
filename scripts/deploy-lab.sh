#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${APP_HOST:?Set APP_HOST to the lab application host without https://}"
REGISTRY_NAMESPACE="${REGISTRY_NAMESPACE:-$(ibmcloud cr namespaces | awk '/^sn-labs-/ {print $1; exit}')}"
test -n "$REGISTRY_NAMESPACE"
export WEB_IMAGE="us.icr.io/$REGISTRY_NAMESPACE/dealership:latest"
export API_IMAGE="us.icr.io/$REGISTRY_NAMESPACE/bestcars-api:latest"
export SENTIMENT_IMAGE="us.icr.io/$REGISTRY_NAMESPACE/bestcars-sentiment:latest"
export APP_HOST
docker build -f server/Dockerfile.lab -t "$WEB_IMAGE" server
(cd server/database && npm ci --omit=dev --no-audit --no-fund && mkdir -p vendor_modules && cp -a node_modules/. vendor_modules/)
docker build -f server/database/Dockerfile.lab -t "$API_IMAGE" server/database
docker build -t "$SENTIMENT_IMAGE" server/djangoapp/microservices
docker push "$WEB_IMAGE"
docker push "$API_IMAGE"
docker push "$SENTIMENT_IMAGE"
if ! kubectl get secret bestcars-secrets >/dev/null 2>&1; then
  kubectl create secret generic bestcars-secrets --from-literal="django-secret=$(openssl rand -hex 32)"
fi
envsubst '${WEB_IMAGE} ${API_IMAGE} ${SENTIMENT_IMAGE} ${APP_HOST}' < server/deployment.yaml | kubectl apply -f -
kubectl rollout status deployment/dealership --timeout=300s
echo 'Deployment ready. Run: kubectl port-forward --address 0.0.0.0 deployment/dealership 8000:8000 3030:3030 5000:5000'
