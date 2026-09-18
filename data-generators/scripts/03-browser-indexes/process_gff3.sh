#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../_paths.sh
source "$SCRIPT_DIR/../_paths.sh"

FTP_URL="http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/"
BASE_URL="http://localhost:3000"
GFF_OUT="${BROWSER_INDEX_OUT}/gff3_files"
LIST_FILE="${BROWSER_INDEX_OUT}/isolate_list.txt"

mkdir -p "$GFF_OUT"

echo "Fetching list of GFF3 isolate names from FTP server..."
curl -s $FTP_URL | grep -oE 'href="([^"]+/)"' | sed 's|href="||; s|/"||' > "$LIST_FILE"

if [ ! -s "$LIST_FILE" ]; then
  echo "Error: No isolate directories found at the FTP location."
  exit 1
fi

while read -r isolate_name; do
  echo "Processing isolate: $isolate_name..."
  mkdir -p "$GFF_OUT/$isolate_name"
  GFF_FILE_URL="${FTP_URL}${isolate_name}/functional_annotation/merged_gff/"

  # Fetch the GFF file name with retries
  retries=3
  for attempt in $(seq 1 $retries); do
    gff_file=$(curl -s $GFF_FILE_URL | grep -oE 'href="[^"]*_annotations\.gff"' | sed 's|href="||' | tr -d '"')
    if [ -n "$gff_file" ]; then
      echo "Found GFF file: $gff_file on attempt $attempt."
      break
    else
      echo "Attempt $attempt: No GFF file found for isolate $isolate_name. Retrying in 5 seconds..."
      sleep 5
    fi
  done

  if [ -z "$gff_file" ]; then
    echo "Error: No GFF file found for isolate $isolate_name after $retries attempts. Skipping."
    continue
  fi

  FULL_GFF_FILE_URL="${GFF_FILE_URL}${gff_file}"
  echo "Downloading from FULL_GFF_FILE_URL: $FULL_GFF_FILE_URL"

  # Download the GFF file with retries
  for attempt in $(seq 1 $retries); do
    wget -q "$FULL_GFF_FILE_URL" -O "$GFF_OUT/$isolate_name/_orig_${gff_file}"
    if [ -s "$GFF_OUT/$isolate_name/_orig_${gff_file}" ]; then
      echo "Downloaded ${gff_file} successfully on attempt $attempt."
      break
    else
      echo "Attempt $attempt: Failed to download ${gff_file}. Retrying in 5 seconds..."
      sleep 5
    fi
  done

  if [ ! -s "$GFF_OUT/$isolate_name/_orig_${gff_file}" ]; then
    echo "Error: ${gff_file} could not be downloaded after $retries attempts or is empty. Skipping."
    continue
  fi

  # Trim the GFF file
  awk '/##FASTA/{exit}1' "$GFF_OUT/$isolate_name/_orig_${gff_file}" > "$GFF_OUT/$isolate_name/trimmed_${isolate_name}.gff"

  # Verify the trimmed file
  if [ ! -s "$GFF_OUT/$isolate_name/trimmed_${isolate_name}.gff" ]; then
    echo "Error: Failed to trim ${gff_file}. Skipping this isolate."
    continue
  fi

  # Generate bgzipped and sorted version of the GFF file
  jbrowse sort-gff "$GFF_OUT/$isolate_name/trimmed_${isolate_name}.gff" > "$GFF_OUT/$isolate_name/${gff_file}"
  bgzip "$GFF_OUT/$isolate_name/${gff_file}"

  # Verify the bgzipped GFF file
  if [ ! -s "$GFF_OUT/$isolate_name/${gff_file}.gz" ]; then
    echo "Error: Failed to create ${gff_file}.gz. Skipping this isolate."
    continue
  fi

  # Generate tabix index file (.tbi)
  tabix -p gff "$GFF_OUT/$isolate_name/${gff_file}.gz"

  # Verify the tabix file
  if [ ! -s "$GFF_OUT/$isolate_name/${gff_file}.gz.tbi" ]; then
    echo "Error: Failed to create ${gff_file}.gz.tbi. Skipping this isolate."
    continue
  fi

  # Generate text index files (.ix and .ixx)
  jbrowse text-index --file "$GFF_OUT/$isolate_name/${gff_file}.gz" --fileId "${isolate_name}_annotations" --out "$GFF_OUT/$isolate_name"

  # Verify text index files
  if [ ! -s "$GFF_OUT/$isolate_name/trix/${gff_file}.gz.ix" ]; then
    echo "Error: Failed to create ${gff_file}.gz.ix. Skipping this isolate."
    continue
  fi
  if [ ! -s "$GFF_OUT/$isolate_name/trix/${gff_file}.gz.ixx" ]; then
    echo "Error: Failed to create ${gff_file}.gz.ixx. Skipping this isolate."
    continue
  fi

  # Handle the metadata file
  meta_json="$GFF_OUT/$isolate_name/sorted_${isolate_name}.gff.gz_meta.json"
  if [ -f "$meta_json" ]; then
    sed -i '' "s|\"localPath\": \".*\"|\"uri\": \"${BASE_URL}/gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz\"|" "$meta_json"
    sed -i '' 's|"locationType": "LocalPathLocation"|"locationType": "UriLocation"|' "$meta_json"
  fi

  # Verify metadata file
  if [ ! -s "$GFF_OUT/$isolate_name/trix/${gff_file}.gz_meta.json" ]; then
    echo "Error: Failed to create ${gff_file}.gz_meta.json. Skipping this isolate."
    continue
  fi

  echo "Processed isolate $isolate_name successfully."
  echo "Files created:"
  ls -lh "$GFF_OUT/$isolate_name"

  # Optional delay to avoid server rate limiting
  sleep 2

done < "$LIST_FILE"

if [ -f "$SCRIPT_DIR/process_essentiality.sh" ]; then
  echo "Starting essentiality GFF3 processing..."
  bash "$SCRIPT_DIR/process_essentiality.sh"
else
  echo "Note: process_essentiality.sh is not present; skipping essentiality GFF3 processing."
fi

echo "GFF3 processing completed. Output: $GFF_OUT"
