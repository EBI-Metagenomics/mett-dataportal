#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../_paths.sh
source "$SCRIPT_DIR/../_paths.sh"

FTP_URL="http://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/"
FASTA_OUT="${BROWSER_INDEX_OUT}/fasta_files"
LIST_FILE="${BROWSER_INDEX_OUT}/fasta_files_list.txt"

mkdir -p "$FASTA_OUT"

echo "Fetching list of FASTA files from FTP server..."
curl -s $FTP_URL | grep -o 'href="[^"]*.fa"' | sed 's/href="//' > "$LIST_FILE"

# process FASTA files
while read -r fasta_file; do
  fasta_file=$(echo "$fasta_file" | tr -d '"')
  isolate_name="${fasta_file%.fa}"
  retries=3  # Number of retry attempts

  echo "Processing $fasta_file for isolate $isolate_name..."
  mkdir -p "$FASTA_OUT/$isolate_name"

  # Attempt to download with retries
  for attempt in $(seq 1 $retries); do
    wget -q "${FTP_URL}${fasta_file}" -O "$FASTA_OUT/$isolate_name/$fasta_file"
    if [ -s "$FASTA_OUT/$isolate_name/$fasta_file" ]; then
      echo "Downloaded $fasta_file successfully on attempt $attempt."
      break
    else
      echo "Attempt $attempt: Failed to download $fasta_file. Retrying in 5 seconds..."
      sleep 5
    fi
  done

  # Final check to skip if download failed after retries
  if [ ! -s "$FASTA_OUT/$isolate_name/$fasta_file" ]; then
    echo "Error: $fasta_file could not be downloaded after $retries attempts. Skipping."
    continue
  fi

  # Generate compressed version of the FASTA file using bgzip
  bgzip -c "$FASTA_OUT/$isolate_name/$fasta_file" > "$FASTA_OUT/$isolate_name/${fasta_file}.gz"

  # Verify the gzipped FASTA file
  if [ ! -s "$FASTA_OUT/$isolate_name/${fasta_file}.gz" ]; then
    echo "Error: Failed to create ${fasta_file}.gz. Skipping this isolate."
    continue
  fi

  # Generate FASTA index file (.fai)
  samtools faidx "$FASTA_OUT/$isolate_name/${fasta_file}.gz"

  # Verify the index file
  if [ ! -s "$FASTA_OUT/$isolate_name/${fasta_file}.gz.fai" ]; then
    echo "Error: Failed to create ${fasta_file}.gz.fai. Skipping this isolate."
    continue
  fi

  # Generate bgzipped version of FASTA index file (.fai.gz)
  bgzip -c "$FASTA_OUT/$isolate_name/${fasta_file}.gz.fai" > "$FASTA_OUT/$isolate_name/${fasta_file}.gz.fai.gz"

  # Verify the bgzipped index file
  if [ ! -s "$FASTA_OUT/$isolate_name/${fasta_file}.gz.fai.gz" ]; then
    echo "Error: Failed to create ${fasta_file}.gz.fai.gz. Skipping this isolate."
    continue
  fi

  echo "Processed $fasta_file for isolate $isolate_name successfully."

  sleep 2

done < "$LIST_FILE"

echo "FASTA processing completed. Output: $FASTA_OUT"
