# MANBAMM data management tools

MANBAMM is a collaborative research project funded by the *Agence Nationale de la Recherche* (ANR). MANBAMM has a Data Management Plan. Scientific data generated in the project will be stored in an organized and reliable manner. Here, we start a collection of software tools, programmed in Python, to maintain, audit and catalogue MANBAMM's data store. These will be command-line tools.

## superhash: checking data integrity

```
python superhash.py --help
```

The superhash result files contain the momentaneous list of all files in the data store, or a part of it, together with the MD5 checksum of each file. These results files are intended to be kept and accumulated externally as metadata to the data store. Data integrity can be verified by intercomparing result files taken at different times. Also, they represent an index of all file present at the moment the superhash list was made.

Pathnames is the file are always stored in POSIX format, even on Windows systems (**TO BE TESTED**).

The file modification times stored in the files, like any other timestamp, are encoded in the ISO format, via `datetime.datetime.isoformat()` method, so that only very little precision is lost (microsecond precision) and the information can be read back into Python using `datetime.datetime.fromisoformat()`.


