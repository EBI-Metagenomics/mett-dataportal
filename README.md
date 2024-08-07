# METT DataPortal Data Portal
The Microbial Ecosystems Transversal Theme, part of the EMBL Programme "Molecules to Ecosystems", focuses on understanding the roles and interactions of microbes within various ecosystems. 
It explores how microbial communities impact their environments and aims to develop methods to modulate microbiomes for beneficial outcomes. 
The research integrates disciplines like genomics, bioinformatics, and ecology, and includes projects such as the MGnify data resource and the TREC expedition. 
The Flagship Project of METT has focused efforts on annotating the genomes of Phocaeicola Vulgatus and Bacteroides uniformis, 
two of the most prevalent and abundant bacterial species of the human microbiome.

There is a normal Django Admin panel as well.

## Development
Install development tools (including pre-commit hooks to run Black code formatting).
```shell
pip install -r requirements-dev.txt
pre-commit install
```

## Use
```shell
source config/secrets.env
python manage.py migrate
python manage.py import_data
python manage.py runserver
```
