#!/bin/bash

FTP_URL="http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/"
LIMIT=10  # limit for dev testing

mkdir -p gff3_files

echo "Fetching list of GFF3 isolate names from FTP server..."
curl -s $FTP_URL | grep -oE 'href="([^"]+/)"' | sed 's|href="||; s|/"||' | head -n $LIMIT > isolate_list.txt

if [ ! -s isolate_list.txt ]; then
  echo "Error: No isolate directories found at the FTP location."
  exit 1
fi

while read -r isolate_name; do
  echo "Processing isolate: $isolate_name..."
  mkdir -p "gff3_files/$isolate_name"
  GFF_FILE_URL="${FTP_URL}${isolate_name}/functional_annotation/merged_gff/"
  gff_file=$(curl -s $GFF_FILE_URL | grep -oE 'href="[^"]*_annotations\.gff"' | sed 's|href="||')
  gff_file=$(echo "$gff_file" | tr -d '"')
  echo "GFF file: $gff_file"
  if [ -z "$gff_file" ]; then
    echo "Error: No GFF file found for isolate $isolate_name. Skipping."
    continue
  fi

  FULL_GFF_FILE_URL="${GFF_FILE_URL}${gff_file}"
  echo "FULL_GFF_FILE_URL: $FULL_GFF_FILE_URL"
  wget -q "$FULL_GFF_FILE_URL" -O "gff3_files/$isolate_name/${gff_file}"

  if [ ! -s "gff3_files/$isolate_name/${gff_file}" ]; then
    echo "Error: ${gff_file} could not be downloaded or is empty. Skipping."
    continue
  fi

  # Triming the GFF file by removing everything after '##FASTA'
  awk '/##FASTA/{exit}1' "gff3_files/$isolate_name/${gff_file}" > "gff3_files/$isolate_name/trimmed_${isolate_name}.gff"

  # Verify
  if [ ! -s "gff3_files/$isolate_name/trimmed_${isolate_name}.gff" ]; then
    echo "Error: Failed to trim ${gff_file}. Skipping this isolate."
    continue
  fi

  # Generate bgzipped and sorted version of the GFF file
  jbrowse sort-gff "gff3_files/$isolate_name/trimmed_${isolate_name}.gff" > "gff3_files/$isolate_name/sorted_${isolate_name}.gff"
  bgzip "gff3_files/$isolate_name/sorted_${isolate_name}.gff"

  # Verify
  if [ ! -s "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz" ]; then
    echo "Error: Failed to create sorted_${isolate_name}.gff.gz. Skipping this isolate."
    continue
  fi

  # Generate tabix (.tbi) file
  tabix -p gff "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz"

  # Verify
  if [ ! -s "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz.tbi" ]; then
    echo "Error: Failed to create sorted_${isolate_name}.gff.gz.tbi. Skipping this isolate."
    continue
  fi

  # Generate an index file (.ix)
  jbrowse text-index --file "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz" --fileId "${isolate_name}_annotations" --out "gff3_files/$isolate_name"

  # Verify  (.ix)
  if [ ! -s "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz.ix" ]; then
    echo "Error: Failed to create sorted_${isolate_name}.gff.gz.ix. Skipping this isolate."
    continue
  fi

  # Verify (.ixx)
  if [ ! -s "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz.ixx" ]; then
    echo "Error: Failed to create sorted_${isolate_name}.gff.gz.ixx. Skipping this isolate."
    continue
  fi

  # Create the metadata file
  cat <<EOT > "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz_meta.json"
{
  "fileName": "sorted_${isolate_name}.gff.gz",
  "description": "GFF3 file for isolate ${isolate_name} with annotations",
  "createdBy": "JBrowse CLI"
}
EOT

  # Verify
  if [ ! -s "gff3_files/$isolate_name/sorted_${isolate_name}.gff.gz_meta.json" ]; then
    echo "Error: Failed to create sorted_${isolate_name}.gff.gz_meta.json. Skipping this isolate."
    continue
  fi

  echo "Processed isolate $isolate_name successfully."
  echo "Files created:"
  ls -lh "gff3_files/$isolate_name"

done < isolate_list.txt

echo "GFF3 processing completed."
