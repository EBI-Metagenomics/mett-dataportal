#!/bin/bash

# Script to copy generated FASTA files to NFS volume (pyhmmer data)
# This script assumes you have a pod running with NFS access

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../_paths.sh
source "$SCRIPT_DIR/../_paths.sh"

# Configuration
POD_NAME="file-copy-pod"
NAMESPACE="mett-dataportal-hl-dev"
LOCAL_OUTPUT_DIR="$FAA_OUT"
NFS_DEST_DIR="/data/pyhmmer/output"

echo "🚀 Starting file copy process..."

# Check if pod is running
echo "📋 Checking if pod $POD_NAME is running..."
if ! kubectl get pod $POD_NAME -n $NAMESPACE | grep -q "Running"; then
    echo "❌ Pod $POD_NAME is not running. Please start it first:"
    echo "   kubectl apply -f $SCRIPT_DIR/file-copy-pod.yml"
    exit 1
fi

echo "✅ Pod is running"

# Create destination directory on NFS
echo "📁 Creating destination directory on NFS..."
kubectl exec $POD_NAME -n $NAMESPACE -- mkdir -p $NFS_DEST_DIR
kubectl exec $POD_NAME -n $NAMESPACE -- mkdir -p $NFS_DEST_DIR/isolates-db

# Copy consolidated files
echo "📋 Copying consolidated files..."
kubectl cp $LOCAL_OUTPUT_DIR/bu_typestrains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_typestrains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_typestrains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_typestrains_deduplicated.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_all_strains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_all_strains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_all_strains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_all_strains_deduplicated.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/pv_typestrains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  pv_typestrains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/pv_typestrains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  pv_typestrains_deduplicated.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/pv_all_strains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  pv_all_strains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/pv_all_strains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  pv_all_strains_deduplicated.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_pv_typestrains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_pv_typestrains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_pv_typestrains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_pv_typestrains_deduplicated.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_pv_all_strains.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_pv_all_strains.faa not found"
kubectl cp $LOCAL_OUTPUT_DIR/bu_pv_all_strains_deduplicated.faa $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/ 2>/dev/null || echo "⚠️  bu_pv_all_strains_deduplicated.faa not found"

# Copy isolates database
echo "📋 Copying isolates database..."
if [ -d "$LOCAL_OUTPUT_DIR/isolates-db" ]; then
    echo "📋 Copying individual isolate files..."
    # Copy all files from isolates-db directory
    for file in $LOCAL_OUTPUT_DIR/isolates-db/*.faa; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "  📄 Copying $filename..."
            kubectl cp "$file" $NAMESPACE/$POD_NAME:$NFS_DEST_DIR/isolates-db/
        fi
    done
else
    echo "⚠️  isolates-db directory not found"
fi

# List files on NFS to verify
echo "📋 Verifying copied files on NFS..."
kubectl exec $POD_NAME -n $NAMESPACE -- ls -la $NFS_DEST_DIR/
if [ -d "$LOCAL_OUTPUT_DIR/isolates-db" ]; then
    echo "📋 Isolates database files:"
    kubectl exec $POD_NAME -n $NAMESPACE -- ls -la $NFS_DEST_DIR/isolates-db/ | head -10
    echo "  ... (showing first 10 files)"
fi

echo "✅ File copy process completed!"
echo "📁 Files are now available on NFS at: $NFS_DEST_DIR"
echo "🔍 You can access them from other pods that mount the same NFS volume (like celery workers)"
echo "📝 The celery worker pod can access these files at: /data/pyhmmer/output/"
