#!/bin/bash

# Generate a Django secret key
echo "Generating Django secret key..."

DJANGO_SECRET_KEY=$(python3 -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
")

echo "Generated Django secret key:"
echo "$DJANGO_SECRET_KEY"
echo ""

# Encode 
ENCODED_SECRET=$(echo -n "$DJANGO_SECRET_KEY" | base64)

echo "Base64 encoded secret key for Kubernetes:"
echo "$ENCODED_SECRET"
echo ""

echo "Update the file k8s/mett-app/overlays/production/mett-django-secret.yaml with this encoded value:"
echo "DJANGO_SECRET_KEY: $ENCODED_SECRET" 