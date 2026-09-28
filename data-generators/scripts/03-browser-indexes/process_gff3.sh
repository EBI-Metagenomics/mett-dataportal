#!/usr/bin/env bash
# Index GFF3 files only. Paths are passed through to run.py.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/run.py" run --only gff "$@"
