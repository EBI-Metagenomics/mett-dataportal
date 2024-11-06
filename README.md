# ME TT Data Portal
The Microbial Ecosystems Transversal Theme, part of the EMBL Programme "Molecules to Ecosystems", focuses on understanding the roles and interactions of microbes within various ecosystems. 
It explores how microbial communities impact their environments and aims to develop methods to modulate microbiomes for beneficial outcomes. 
The research integrates disciplines like genomics, bioinformatics, and ecology, and includes projects such as the MGnify data resource and the TREC expedition. 
The Flagship Project of METT has focused efforts on annotating the genomes of Phocaeicola Vulgatus and Bacteroides uniformis, 
two of the most prevalent and abundant bacterial species of the human microbiome.

There is a normal Django Admin panel as well.

## Requirements

- **Python Version**: This project requires **Python 3.12**. Please ensure that you have this version installed to avoid compatibility issues. 
- You can download the latest version [here](https://www.python.org/downloads/).

## In Development - Intermediate Stage 


### Development Environment
Dependencies installation -
```shell
pip install -r requirements-dev.txt
pre-commit install
```

### Steps to bring up the local environment 
- [X] Migration files are in repo. use ```python manage.py migrate``` to setup the tables
- [X] Use import scripts to import the data from FTP server. Ref: [How to import](./data-generators/import-scripts/README.md)
- [X] Create indexes for Fasta and GFF files. Ref: [How to generate indexes](./data-generators/index-scripts/README.md)
- [X] Run djando sever ```python manage.py runserver```
- [X] Run react **./dataportal-app** app using ```npm start```

### Configuration
We use [Pydantic](https://pydantic-docs.helpmanual.io/) to formalise Config files.
- `config/local.env` as a convenience for env vars.

### Import Species, Strains and Annotations
Scripts -
```shell
$ python manage.py import_species --csv ./species.csv
$ python manage.py import_strains_contigs --ftp-server "ftp.ebi.ac.uk" --ftp-directory "/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/" --set-type-strains BU_ATCC8492 PV_ATCC8482
$ python manage.py import_annotations --ftp-server ftp.ebi.ac.uk --ftp-directory /pub/databases/mett/annotations/v1_2024-04-15/ 

```

### Code style
Use [Black](https://black.readthedocs.io/en/stable/).
Use [Ruff](https://docs.astral.sh/ruff/installation/).
These are both configured if you install the pre-commit tools as above.

To manually run them:
`black .` and `ruff check --fix`.

## Testing
```shell
pip install -r requirements-dev.txt
pytest
```

## Initial Database table setup
```shell
python manage.py makemigrations
python manage.py makemigrations dataportal --empty
python manage.py migrate
```

