## Intermediate scripts

These scripts are to generate the indexed files for testing and later can be utilized to enhance the data pipeline itself -

Run below scripts to have the indexes generated -
```bash
$ cd data-generators/scripts/03-browser-indexes
$ ./process_fasta.sh
$ ./process_gff3.sh
```

Outputs go to `data-generators/data/generated/browser-indexes/` (override with `BROWSER_INDEX_OUT`).

`process_gff3.sh` used to call `process_essentiality.sh`; that script is not in the repo, so the GFF step skips it if missing.


### Process Brief

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

### Additional Tracks

