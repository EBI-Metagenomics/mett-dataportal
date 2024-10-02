## Intermediate scripts

These scripts are to generate the indexed files for testing and later can be utilized to enhance the data pipeline
itself -

#### Fasta Files --
* bgzip fasta
* FASTA index file (.fai)
* bgzip FASTA index file (.fai.gz)
#### GFF Files --
* Trim the GFF file by removing everything after ‘##FASTA’
* Generate bgzipped and sorted (jbrowse sort-gff) version of the GFF file
* Generate tabix (.tbi) file
*  Generate an index file (.ix)
* Generate an auxiliary index file (.ixx)
* Generate the metadata file (.gff.gz_meta.json)

### Fasta processing script

- [ ] Read dynamically from FTP server with given path conventions.
      All fasta files (*.fa) are available at ftp location - http://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/
- [ ] Optionally limit it to first 10 genomes
- [ ] Generate compressed version of the FASTA file using bgzip
  ```bash 
  $ bgzip -c input.fa > input.fa.gz
  ```
- [ ] Generate FASTA index file (.fai)
  ```bash 
  $ samtools faidx input.fa.gz
  ```
- [ ] Generate bgzipped version of FASTA index file (.fai.gz)
  ```bash 
  $ bgzip -c input.fa.fai > input.fa.fai.gz
  ```

### GFF3 processing script

- [ ] Read dynamically from FTP server with given path conventions
      All gff files (*.gff) are available at ftp location - 
        http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/<isolate-name>/functional_annotation/merged_gff/*_annotations.gff.gff
- [ ] Optionally limit it to annotations for first 10 genomes only
- [ ] Trim the GFF file by removing everything after '##FASTA'
  ```bash 
  $ awk '/##FASTA/{exit}1' input.gff > trimmed.gff
  ```
- [ ] Generate bgzipped and sorted version of the GFF file
  ```bash 
  $ jbrowse sort-gff input.gff > sorted.gff
  $ bgzip sorted.gff
  ```
- [ ] Generate tabix (.tbi) file - an index for the sorted.gff.gz
  ```bash 
  $ tabix -p gff sorted.gff.gz
  ```
- [ ] Generate an index file (.ix) that enables searching text within the sorted.gff.gz
  ```bash 
  $ jbrowse text-index -i sorted.gff.gz -o sorted.gff.gz.ix
  ```
- [ ] Generate an auxiliary index file (.ixx) to speed up the text search process
  ```bash 
  $ jbrowse text-index -i sorted.gff.gz -o sorted.gff.gz.ixx
  ```
- [ ] Generate the metadata file (sorted.gff.gz_meta.json) about the indexed GFF file
  ```bash 
  ??? 
  ```


