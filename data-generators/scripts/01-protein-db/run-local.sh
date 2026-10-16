#!/usr/bin/env bash
# Stage every isolate listed in sources.tsv, then merge and index.
#
#   python3 run.py plan --batch all --jobs sources.tsv
#   ./run-local.sh
#   ./run-local.sh --fetch
#   ./run-local.sh --fetch sources.tsv ./chunks ../../data/generated/protein-db
#
# --fetch is for a machine without /pub/databases mounted. It downloads each
# missing HD FASTA from https://ftp.ebi.ac.uk/pub/databases/mett into
# data/generated/protein-db/faa-cache. The 20hm paths are not on that site.

set -euo pipefail

cd "$(dirname "$0")"

fetch=0
positional=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fetch)
      fetch=1
      shift
      ;;
    *)
      positional+=("$1")
      shift
      ;;
  esac
done

sources="${positional[0]:-sources.tsv}"
chunks="${positional[1]:-chunks}"
out="${positional[2]:-../../data/generated/protein-db}"

if [[ ! -f "$sources" ]]; then
  echo "Missing ${sources}. Create it with: python3 run.py plan --batch all --jobs sources.tsv" >&2
  exit 1
fi

mkdir -p "$chunks"

tail -n +2 "$sources" | while IFS=$'\t' read -r isolate species faa type_strain collection _name; do
  flag=()
  if [[ "$type_strain" == "true" ]]; then
    flag=(--type-strain)
  fi
  if [[ "$fetch" -eq 1 ]]; then
    flag+=(--fetch)
  fi
  python3 run.py stage \
    --faa "$faa" \
    --isolate "$isolate" \
    --species "$species" \
    --collection "$collection" \
    "${flag[@]}" \
    --out "${chunks}/${isolate}.jsonl"
done

python3 run.py merge --chunks "$chunks" --out "$out"
python3 run.py index \
  --faa "${out}/mett_proteins.faa" \
  --members "${out}/members.tsv" \
  --out "$out"
