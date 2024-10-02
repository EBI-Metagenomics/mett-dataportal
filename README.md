# ME TT Data Portal
The Microbial Ecosystems Transversal Theme, part of the EMBL Programme "Molecules to Ecosystems", focuses on understanding the roles and interactions of microbes within various ecosystems. 
It explores how microbial communities impact their environments and aims to develop methods to modulate microbiomes for beneficial outcomes. 
The research integrates disciplines like genomics, bioinformatics, and ecology, and includes projects such as the MGnify data resource and the TREC expedition. 
The Flagship Project of METT has focused efforts on annotating the genomes of Phocaeicola Vulgatus and Bacteroides uniformis, 
two of the most prevalent and abundant bacterial species of the human microbiome.

There is a normal Django Admin panel as well.


## In Development - Intermediate Stage 

### Steps to bring up the local environment 
- [ ] Migration files are in repo. use ```python manage.py migrate``` to setup the tables
- [ ] Use import scripts to import the data from FTP server. Ref: [How to import](./data-generators/import-scripts/README.md)
- [ ] Create indexes for Fasta and GFF files. Ref: [How to generate indexes](./data-generators/index-scripts/README.md)
- [ ] Run djando sever ```python manage.py runserver```
- [ ] Run react app using ```npm start```


## Development
Dependencies installation -
```shell
pip install -r requirements-dev.txt
pre-commit install
```

## Initial Database table setup
```shell
python manage.py makemigrations
python manage.py makemigrations dataportal --empty
python manage.py migrate

```
