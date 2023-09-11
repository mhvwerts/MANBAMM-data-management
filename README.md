# MANBAMM data management tools

MANBAMM is a collaborative research project funded by the *Agence Nationale de la Recherche* (ANR). MANBAMM has a Data Management Plan. Scientific data generated in the project will be stored in an organized and reliable manner. Here, we start a collection of software tools, programmed in Python, to maintain, audit and catalogue MANBAMM's data store. These will be command-line tools.

## General warning!
**Use at your own risk**. *Make sure you have good back-ups of your data. The tools presented here are under development, and have not been thoroughly tested under 'real life' conditions. In particular, at present, they have been used only with file collections under Linux (ext4) and Windows (NTFS) and may not yet work properly with MacOS X.* 

## Special warning for Windows users

Windows has a [maximum path length limitation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation), limiting the total length of a path to a file to 260 characters. This can cause problems for data-sets in which files with long names are stored in a deep hierarchy of sub-directories. In that case, the scripts for data management may crash, citing that some file could not be found, even though it is there when you look for it.

Starting from Windows 10, version 1607, the path length limitation has been removed, but you have to 'opt-in', which involves [editing the registry](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=powershell#enable-long-paths-in-windows-10-version-1607-and-later). For Windows 10 Pro, there is also a [GUI-guided procedure using the 'Group Policy Editor'](https://www.howtogeek.com/266621/how-to-make-windows-10-accept-file-paths-over-260-characters/) to remove the maximum path length limitation.


## superhash: checking data integrity

`superhash` is a utility for generating index files containing MD5 checksums of all files in the source directory and its sub-directories. It provides a way for thoroughly testing data integrity and machine-readability of all data in the collection. It also helps to track the evolution of the catalogue of data files as the collection develops.

The superhash result files contain the momentaneous list of all files in the data store, or a part of it, together with the MD5 checksum of each file. These results files are intended to be kept and accumulated externally as metadata to the data store. Data integrity can be verified by intercomparing result files taken at different moments. Also, they represent an index of all file present at the moment the superhash list was made.

### superhash usage

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

The result files are always encoded in UTF-8 (what else?), and pathnames in the file are always stored in POSIX format, even on Windows systems, in order to ensure cross-platform operation.

The file modification times stored in the files, like any other timestamp, are encoded in the ISO format, via `datetime.datetime.isoformat()` method, so that only very little precision is lost (microsecond precision) and the information can be read back into Python using `datetime.datetime.fromisoformat()`.


### superhash workflow

The typical use scenario of `superhash` and `superhash-check` starts with running `superhash` in order to generate index files containing the information on the tree structure and all files starting from a source directory. These superhash index files can be generated from an original source, and its back-up copies. It can also be generated from any subdirectory within the source (by specifying that subdirectory as the source when running `superhash`). The index files use relative  paths, and `superhash-check` can work with paths relative to those (relative) paths.

Generation of index files can take a long time, especially for large data sets, since all files are read entirely to generate an MD5 checksum. This checks that all files are indeed readable, and allows to verify that data integrity has been preserved between different copies of the same file. If only the directory tree structure is needed, index file generation can become way much faster by specifying the `--nohash` option. This is fast but of course does not check file integrity.

Once a pair of index files of the same data set is available (these can be the same copy at different times, or two different copies), the entries in the index files can be compared using `superhash-check`. This script will take one index as the reference (`file1`) and scan the entry lines in the second file (`file2`). Each entry in `file2` will be looked up in the reference `file1` and compared. If differing MD5 checksums are found, the error will be reported. Entries that are in `file2` but not in `file1` will be reported missing. These entries may for example represent new files that have been added. It is possible to retrieve a list of the missing lines as a `.tsv` file.

As can be concluded from the previous paragraph, the two index files are not treated symmetrically by `superhash-check`. In certain cases, it may be helpful to run `superhash-check` twice, exchanging the index files. This can happen if data sets become disorganized by changing directory names, deleting files etc. Watch out for headaches and try to keep your datasets (and its copies) organized. `superhash` does not do that for you...

### superhash-check usage

```
python superhash-check.py --help
usage: superhash-check.py [-h] [-m MISSING] file1 file2

positional arguments:
  file1                 first superhash file
  file2                 2nd superhash file

optional arguments:
  -h, --help            show this help message and exit
  -m MISSING, --missing MISSING
                        file to write the list of missing entries to
```



## safename: filenames that are compatible across Windows, MacOSX and Linux

Local copies of (parts of) the datafile collection can be stored on Windows, MacOSX, or Linux. The characters allowed in file and directory names are not the same across these systems. We should therefore ensure that the names of files and directories ('pathnames') have only characters that are compatible with all systems. This can be done with the aid of `safename`.

`safename` currently identifies four types of problems:
1. presence of 'non-printable' characters in names ('UNPRINTABLE'). Fatal error.
2. leading or trailing whitespace (*e.g.*, spaces) in a pathname ('WHITESPACE')
3. presence of characters  `< > : " / \ | ? *` ('BADCHARS')
4. symbolic links ('SYMLINK')

### safename usage

```
python safename.py --help
usage: safename.py [-h] [-r] src_dir

Check for compatibility problems in the names of files in a directory tree.

WARNING: with the -r / --repair option activated, this script may
         irreversibly alter the contents of your directory tree.


positional arguments:
  src_dir       Source directory to be scanned.

optional arguments:
  -h, --help    show this help message and exit
  -r, --repair  Fix detected problems, ONE AT A TIME.

safename currently identifies four types of problems:
    1. Presence of 'non-printable' characters in names ('UNPRINTABLE'). Fatal
       error.
    2. Leading or trailing whitespace (*e.g.*, spaces) in a pathname
       ('WHITESPACE')
    3. Presence of characters  `< > : " / \ | ? *` ('BADCHARS')
    4. Symbolic links ('SYMLINK')

```


## Requirements

At present, the only "non-standard" library to be installed is ``tqdm``. This is specified in ``requirements.txt``.

In this repository, we also include a file ``MANBAMM-full-requirements.txt`` which contains the full list of ``conda`` packages (``conda-forge`` channel) that a standard MANBAMM Python installation needs.

