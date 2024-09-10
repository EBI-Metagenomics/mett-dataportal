

### just execute without voila
```bash
$ jupyter nbconvert --to notebook --execute --output result.ipynb annotations-import.ipynb
```

### voila timeout handling
```bash
$ voila --MappingKernelManager.kernel_timeout=1800 (30 mins)
```