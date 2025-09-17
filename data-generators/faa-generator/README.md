## pyhmmer tests

We recently had a quick meeting to chat about some implementation strategies. To get HMMER up and running, we’ll need nodes with more than 20GB of RAM for a protein database that’s around 15 million entries—similar in size to METT. It’s important that these nodes are always operational, which brings up some cost considerations if we think about moving to the cloud.

Another point to keep in mind is that for METT, we’re expecting a pretty low number of searches on the METT. After some brainstorming, we figured that the most straightforward approach would be to set up a simple configuration using Django + Celery + PyHMMER. PyHMMER will provide with most of the features of the HMMER hits Score tab, but the taxonomy and domain ones won’t as those are specific for HMMER-Web. Another consideration is that the download files will have to be created in a separate task, after the search is compelte. Our plan is to prototype this Django + Celety + PyHMMER combination; we can re-use some of the HMMER-Web UI components.

On the performance, we need to benchmark how PyHMMER behaves as running on a largue number of proteins tends to be strongly IO bound (that is the reason for HMMER daemon to exist).

### Create conda environment -

```bash
$ conda create -n pyhmmer python=3.13.3
```

### Install pyhmmer
```bash
$ pip3 install pyhmmer==0.11.1
```
or 
```bash
$ pip3 install -r requirements.txt
```

### Reference Data Locations

#### FTP Locations -

```bash
http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/
e.g. http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/prokka/BU_ATCC8492.faa
```

#### Codon Nodes ($ ssh codon-login)

```bash
$ cd /hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_uniformis_mags_mettannotator_results/
$ cd /hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_uniformis_mags_mettannotator_results/
$ cd /hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_vulgatus_mags_mettannotator_results/
$ cd /hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_vulgatus_mags_mettannotator_results2/
```

#### Import and consolidate the sequence data
```bash
$ cd ./data-generators/faa-generator
$ python ./run_pipeline.py
```

#### Copy deduplicated files on NFS dev
##### Spwan the test pod
```bash
$ cd ./data-generators/faa-generator
$ kubectl apply -f file-copy-pod.yml
```

##### Copy the files
```bash
$ cd ./data-generators/faa-generator
$ ./copy-files-to-nfs.sh
```


#### Set up the test environment

##### local environment

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
source ~/.bashrc
conda create -n pyhmmer python=3.13.3
conda activate pyhmmer

conda install -c conda-forge cmake gcc numpy psutil
pip install pyhmmer
```
##### run the tasks on SLURM

```bash
$ scp -r ~/Documents/ws/work/pyhmmer-tests vikasg@codon-login:/homes/vikasg/pyhmmer-tests
$ srun --cpus-per-task=8 --mem=16G --time=01:00:00 --pty bash
$ conda activate pyhmmer
$ python pyhmmer_benchmark.py
```


#### Online References (Initial)

[X] https://pyhmmer.readthedocs.io/en/stable/api/hmmer/seq.html
[X] https://pyhmmer.readthedocs.io/en/stable/api/plan7/results.html#pyhmmer.plan7.TopHits
[X] http://eddylab.org/software/hmmer/Userguide.pdf [page 139]
[X] https://www.ebi.ac.uk/Tools/hmmer/results/f3aff4f2-89a7-4a28-abe5-e432924de043/score