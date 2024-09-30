#!/bin/bash

FTP_URL="http://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/"
LIMIT=10  # limit genomes to process for dev testing

mkdir -p fasta_files

echo "Fetching list of FASTA files from FTP server..."
curl -s $FTP_URL | grep -o 'href="[^"]*.fa"' | sed 's/href="//' | head -n $LIMIT > fasta_files_list.txt

# process FASTA files
while read -r fasta_file; do
  fasta_file=$(echo "$fasta_file" | tr -d '"')
  isolate_name="${fasta_file%.fa}"

  echo "Processing $fasta_file for isolate $isolate_name..."
  mkdir -p "fasta_files/$isolate_name"
  wget -q "${FTP_URL}${fasta_file}" -O "fasta_files/$isolate_name/$fasta_file"

  # Check if the file was downloaded successfully and is not empty
  if [ ! -s "fasta_files/$isolate_name/$fasta_file" ]; then
    echo "Error: $fasta_file could not be downloaded or is empty. Skipping."
    continue
  fi

  # Generate compressed version of the FASTA file using bgzip
  bgzip -c "fasta_files/$isolate_name/$fasta_file" > "fasta_files/$isolate_name/${fasta_file}.gz"

  # Verify the gzipped FASTA file
  if [ ! -s "fasta_files/$isolate_name/${fasta_file}.gz" ]; then
    echo "Error: Failed to create ${fasta_file}.gz. Skipping this isolate."
    continue
  fi

  # Generate FASTA index file (.fai)
  samtools faidx "fasta_files/$isolate_name/${fasta_file}.gz"

  # Verify the index file
  if [ ! -s "fasta_files/$isolate_name/${fasta_file}.gz.fai" ]; then
    echo "Error: Failed to create ${fasta_file}.gz.fai. Skipping this isolate."
    continue
  fi

  # Generate bgzipped version of FASTA index file (.fai.gz)
  bgzip -c "fasta_files/$isolate_name/${fasta_file}.gz.fai" > "fasta_files/$isolate_name/${fasta_file}.gz.fai.gz"

  # Verify the bgzipped index file
  if [ ! -s "fasta_files/$isolate_name/${fasta_file}.gz.fai.gz" ]; then
    echo "Error: Failed to create ${fasta_file}.gz.fai.gz. Skipping this isolate."
    continue
  fi

  echo "Processed $fasta_file for isolate $isolate_name successfully."
  echo "Files created:"
  ls -lh "fasta_files/$isolate_name"

done < fasta_files_list.txt

echo "FASTA processing completed."
