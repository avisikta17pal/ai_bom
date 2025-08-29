#!/usr/bin/env bash
set -euo pipefail
IMAGE_BACKEND=${IMAGE_BACKEND:-your-org/ai-bom-backend}
TAG=${TAG:-latest}

echo "Building backend image ${IMAGE_BACKEND}:${TAG}"
docker build -t ${IMAGE_BACKEND}:${TAG} backend

echo "Pushing backend image ${IMAGE_BACKEND}:${TAG}"
# docker push ${IMAGE_BACKEND}:${TAG}

echo "Done."