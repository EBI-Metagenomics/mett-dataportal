# Shared data-generators paths. Source from any script under scripts/.
# Override with FAA_OUT, STRING_INPUT_DIR, STRING_OUT, BROWSER_INDEX_OUT, QC_OUT.
_PATHS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_GENERATORS_ROOT="$(cd "$_PATHS_DIR/.." && pwd)"

FAA_OUT="${FAA_OUT:-$DATA_GENERATORS_ROOT/data/generated/faa}"
STRING_INPUT_DIR="${STRING_INPUT_DIR:-$DATA_GENERATORS_ROOT/data/inputs/stringdb}"
STRING_OUT="${STRING_OUT:-$DATA_GENERATORS_ROOT/data/generated/string-mapping}"
BROWSER_INDEX_OUT="${BROWSER_INDEX_OUT:-$DATA_GENERATORS_ROOT/data/generated/browser-indexes}"
QC_OUT="${QC_OUT:-$DATA_GENERATORS_ROOT/data/generated/qc}"
