#!/bin/bash
# Build and push React Docker image
DOCKER_IMAGE_NAME=microbiome-informatics/mett-dataportal-react
docker build -t $DOCKER_IMAGE_NAME -f dataportal-app/Dockerfile .
# docker push $DOCKER_IMAGE_NAME
