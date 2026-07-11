#!/usr/bin/env bash
set -euo pipefail

# Build and push the AMD Track 2 submission image.
# Run this on a machine with Docker installed and logged into Docker Hub.

IMAGE_TAG="${IMAGE_TAG:-your-registry/amd-track2-agent-v2:latest}"

echo "Building $IMAGE_TAG for linux/amd64..."
docker buildx build --platform linux/amd64 -t "$IMAGE_TAG" --push .

echo "Done. Image pushed to $IMAGE_TAG"
