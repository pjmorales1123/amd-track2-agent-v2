@echo off
REM Build and push the AMD Track 2 submission image.
REM Run this on a machine with Docker installed and logged into Docker Hub.

if "%IMAGE_TAG%"=="" set IMAGE_TAG=your-registry/amd-track2-agent-v2:latest

echo Building %IMAGE_TAG% for linux/amd64...
docker buildx build --platform linux/amd64 -t %IMAGE_TAG% --push .

echo Done. Image pushed to %IMAGE_TAG%
