#!/bin/bash

FTP_URL="http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/"
BASE_URL="http://localhost:3000"

mkdir -p gff3_files

echo "Fetching list of GFF3 isolate names from FTP server..."
curl -s $FTP_URL | grep -oE 'href="([^"]+/)"' | sed 's|href="||; s|/"||' > isolate_list.txt

if [ ! -s isolate_list.txt ]; then
  echo "Error: No isolate directories found at the FTP location."
  exit 1
fi

while read -r isolate_name; do
  echo "Processing isolate: $isolate_name..."
  mkdir -p "gff3_files/$isolate_name"
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
    wget -q "$FULL_GFF_FILE_URL" -O "gff3_files/$isolate_name/_orig_${gff_file}"
    if [ -s "gff3_files/$isolate_name/_orig_${gff_file}" ]; then
      echo "Downloaded ${gff_file} successfully on attempt $attempt."
      break
    else
      echo "Attempt $attempt: Failed to download ${gff_file}. Retrying in 5 seconds..."
      sleep 5
    fi
  done

  if [ ! -s "gff3_files/$isolate_name/_orig_${gff_file}" ]; then
    echo "Error: ${gff_file} could not be downloaded after $retries attempts or is empty. Skipping."
    continue
  fi

  # Trim the GFF file
  awk '/##FASTA/{exit}1' "gff3_files/$isolate_name/_orig_${gff_file}" > "gff3_files/$isolate_name/trimmed_${isolate_name}.gff"

  # Verify the trimmed file
  if [ ! -s "gff3_files/$isolate_name/trimmed_${isolate_name}.gff" ]; then
    echo "Error: Failed to trim ${gff_file}. Skipping this isolate."
    continue
  fi

  # Generate bgzipped and sorted version of the GFF file
  jbrowse sort-gff "gff3_files/$isolate_name/trimmed_${isolate_name}.gff" > "gff3_files/$isolate_name/${gff_file}"
  bgzip "gff3_files/$isolate_name/${gff_file}"

  # Verify the bgzipped GFF file
  if [ ! -s "gff3_files/$isolate_name/${gff_file}.gz" ]; then
    echo "Error: Failed to create ${gff_file}.gz. Skipping this isolate."
    continue
  fi

  # Generate tabix index file (.tbi)
  tabix -p gff "gff3_files/$isolate_name/${gff_file}.gz"

  # Verify the tabix file
  if [ ! -s "gff3_files/$isolate_name/${gff_file}.gz.tbi" ]; then
    echo "Error: Failed to create ${gff_file}.gz.tbi. Skipping this isolate."
    continue
  fi

  # Generate text index files (.ix and .ixx)
  jbrowse text-index --file "gff3_files/$isolate_name/${gff_file}.gz" --fileId "${isolate_name}_annotations" --out "gff3_files/$isolate_name"

  # Verify text index files
  if [ ! -s "gff3_files/$isolate_name/trix/${gff_file}.gz.ix" ]; then
    echo "Error: Failed to create ${gff_file}.gz.ix. Skipping this isolate."
    continue
  fi
  if [ ! -s "gff3_files/$isolate_name/trix/${gff_file}.gz.ixx" ]; then
    echo "Error: Failed to create ${gff_file}.gz.ixx. Skipping this isolate."
    continue
  fi

  # Handle the metadata file
  meta_json="gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz_meta.json"
  if [ -f "$meta_json" ]; then
    sed -i '' "s|\"localPath\": \".*\"|\"uri\": \"${BASE_URL}/gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz\"|" "$meta_json"
    sed -i '' 's|"locationType": "LocalPathLocation"|"locationType": "UriLocation"|' "$meta_json"
  fi

  # Verify metadata file
  if [ ! -s "gff3_files/$isolate_name/trix/${gff_file}.gz_meta.json" ]; then
    echo "Error: Failed to create ${gff_file}.gz_meta.json. Skipping this isolate."
    continue
  fi

  echo "Processed isolate $isolate_name successfully."
  echo "Files created:"
  ls -lh "gff3_files/$isolate_name"

  # Optional delay to avoid server rate limiting
  sleep 2

done < isolate_list.txt

echo "Starting essentiality GFF3 processing..."
bash ./process_essentiality.sh

echo "GFF3 processing completed."
