#!/bin/bash

# Warren Bot Docker Build Script
# This script builds the Warren Bot Docker image with proper tags

set -e

# Configuration
IMAGE_NAME="warren-bot"
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
REGISTRY=${DOCKER_REGISTRY:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Warren Bot Docker Image${NC}"
echo "Version: $VERSION"
echo "Image: $IMAGE_NAME"

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "$IMAGE_NAME:latest" -t "$IMAGE_NAME:$VERSION" .

# If registry is set, also tag for registry
if [ ! -z "$REGISTRY" ]; then
    echo -e "${YELLOW}Tagging for registry: $REGISTRY${NC}"
    docker tag "$IMAGE_NAME:latest" "$REGISTRY/$IMAGE_NAME:latest"
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY/$IMAGE_NAME:$VERSION"
fi

echo -e "${GREEN}Build completed successfully!${NC}"
echo "Available tags:"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Optional: Run a quick test
echo -e "${YELLOW}Testing image...${NC}"
if docker run --rm "$IMAGE_NAME:latest" python -c "import warren_bot; print('Import test passed')"; then
    echo -e "${GREEN}Import test passed!${NC}"
else
    echo -e "${RED}Import test failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Docker build and test completed successfully!${NC}"
echo ""
echo "To run the bot:"
echo "  docker-compose up -d"
echo ""
echo "To push to registry (if configured):"
if [ ! -z "$REGISTRY" ]; then
    echo "  docker push $REGISTRY/$IMAGE_NAME:latest"
    echo "  docker push $REGISTRY/$IMAGE_NAME:$VERSION"
else
    echo "  Set DOCKER_REGISTRY environment variable first"
fi