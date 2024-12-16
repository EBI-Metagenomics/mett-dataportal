#!/bin/bash

ESSENTIALITY_OUTPUT_DIR="gff3_files/essentiality"
ESSENTIALITY_SCRIPT="generate_essentiality_gff3.py"  # Your existing Python script


mkdir -p "$ESSENTIALITY_OUTPUT_DIR"

# Generate essentiality GFF3 files
echo "Generating essentiality GFF3 files..."
python "$ESSENTIALITY_SCRIPT"

# Process each generated essentiality GFF3 file
for essentiality_gff in *_essentiality.gff3; do
  strain_name=$(echo "$essentiality_gff" | cut -d'_' -f1)
  output_dir="$ESSENTIALITY_OUTPUT_DIR/$strain_name"

  mkdir -p "$output_dir"

  # Copy the essentiality GFF3 file to the output directory
  cp "$essentiality_gff" "$output_dir/"

  # Compress the GFF3 file using bgzip
  echo "Compressing $essentiality_gff..."
  bgzip -c "$output_dir/$essentiality_gff" > "$output_dir/${essentiality_gff}.gz"

  # Index the compressed file using tabix
  echo "Indexing $essentiality_gff.gz..."
  tabix -p gff "$output_dir/${essentiality_gff}.gz"

  # Verify the indexed file
  if [ ! -s "$output_dir/${essentiality_gff}.gz.tbi" ]; then
    echo "Error: Failed to create index for ${essentiality_gff}.gz. Skipping."
    continue
  fi

#  # NOT REQUIRED FOR NOW --- Generate text index files (.ix and .ixx) for each essentiality GFF3 file
#  echo "Generating text index for $essentiality_gff.gz..."
#  jbrowse text-index --file "$output_dir/${essentiality_gff}.gz" --fileId "${strain_name}_essentiality" --out "$output_dir"
#
#  # Verify the text index files
#  if [ ! -s "$output_dir/trix/${essentiality_gff}.gz.ix" ]; then
#    echo "Error: Failed to create ${essentiality_gff}.gz.ix. Skipping."
#    continue
#  fi
#  if [ ! -s "$output_dir/trix/${essentiality_gff}.gz.ixx" ]; then
#    echo "Error: Failed to create ${essentiality_gff}.gz.ixx. Skipping."
#    continue
#  fi

  echo "Essentiality file processed: $output_dir/${essentiality_gff}.gz"
done

echo "Essentiality GFF3 processing completed."
