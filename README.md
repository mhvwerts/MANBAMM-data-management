# MANBAMM data management tools

MANBAMM is a collaborative research project funded by the *Agence Nationale de la Recherche* (ANR). MANBAMM has a Data Management Plan. Scientific data generated in the project will be stored in an organized and reliable manner. Here, we start a collection of software tools, programmed in Python, to maintain, audit and catalogue MANBAMM's data store. These will be command-line tools.

## superhash: checking data integrity

`superhash` is a utility for generating index files containing MD5 checksums of all files in the source directory and its sub-directories.



### usage

```
python superhash.py --help
usage: superhash.py [-h] [-n] [-o OUTPATH] src_dir

positional arguments:
  src_dir               source directory to be scanned

optional arguments:
  -h, --help            show this help message and exit
  -n, --nohash          do not calculate hashes, only generate file info tree
  -o OUTPATH, --outpath OUTPATH
                        path or pathname of result file
```

The `OUTPATH` can either specify the pathname of a file to be created (or to be overwritten) or point to a specific directory, in which then an approriately named result file is created. The latter is recommended (*i.e.* `superhash` will generate the name).

The superhash result files contain the momentaneous list of all files in the data store, or a part of it, together with the MD5 checksum of each file. These results files are intended to be kept and accumulated externally as metadata to the data store. Data integrity can be verified by intercomparing result files taken at different moments. Also, they represent an index of all file present at the moment the superhash list was made.

Pathnames is the file are always stored in POSIX format, even on Windows systems (**TO BE TESTED**).

The file modification times stored in the files, like any other timestamp, are encoded in the ISO format, via `datetime.datetime.isoformat()` method, so that only very little precision is lost (microsecond precision) and the information can be read back into Python using `datetime.datetime.fromisoformat()`.

