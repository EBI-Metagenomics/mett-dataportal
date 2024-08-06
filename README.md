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

### Code style
Use [Black](https://black.readthedocs.io/en/stable/).
Use [djLint](https://djlint.com/).
These are both configured if you install the pre-commit tools as above.

To manually run them:
`black .` and `djlint . --extension=html --lint` (or `--reformat`).

### Fake data
Once a database is created and migrated (see below), there is a management command to fill the database
with some minimal fake data for development ease. 
```shell
python manage.py generate_dev_data
```

## Testing
```shell
# You most likely need (see below):
#   brew install chromedriver
pip install -r requirements-dev.txt
pytest
```

### Chrome Driver for web interface tests
The web interface tests need the Chrome browser and `chromedriver` to communicate with the browser.
To install `chromedriver` on a Mac or Linux machine, [use the Homebrew formula](https://formulae.brew.sh/cask/chromedriver)
or any other sensible installation method. On GitHub Actions, a "Setup Chromedriver" action step exists for this.
On a Mac, you’ll probably get Gate Keeper permissions problems running `chromedriver`; so:
```shell
which chromedriver  # probably: /usr/local/bin/chromedriver
spctl --add /usr/local/bin/chromedriver
```
If this doesn't work, `open /usr/local/bin`, then find `chromedriver` in Finder, right click, Open.

## Configuration
We use [Pydantic](https://pydantic-docs.helpmanual.io/) to formalise Config files.
Configuration is split between:
- `config/local.env` as a convenience for env vars.
- `config/data_config.json` contains what are expected to be somewhat change-able config options.
- `config/secrets.env` is needed during development, whilst some data are private.

## Use
```shell
source config/secrets.env
python manage.py migrate
python manage.py import_data
python manage.py runserver
```
