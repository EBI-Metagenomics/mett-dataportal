

### dependency imports
```bash
$ pip install -r ./requirements.txt
```

### data import sequence

#### Import Species data

```bash
$ python import-species.py
```

#### Import Strains data

```bash
$ python import-strains-contigs.py
$ python set-type-strains.py
```

#### Import Genes data

```bash
$ python import-annotations.py
```