# MANBAMM data management tools

MANBAMM is a collaborative research project funded by the *Agence Nationale de la Recherche* (ANR). MANBAMM has a Data Management Plan. Scientific data generated in the project will be stored in an organized and reliable manner. 

Here, we present an evolving collection of software tools, programmed in Python, to maintain, audit and catalogue MANBAMM's data store. These will be command-line tools.



## Contents

- [Management of (large) collections of data-files](./collection_management): verifying data integrity, naming files for cross-platform use, packing together many small data-files
- [Conversion of proprietary instrument file formats into open formats](./file_conversion)


## Requirements

We have included a file ``MANBAMM-full-requirements.txt`` which contains the full list of ``conda`` packages (``conda-forge`` channel) constituting a standard MANBAMM Python installation.



## General warning!
**Use at your own risk**. *Make sure you have good back-ups of your data. The tools presented here are under development, and have not been thoroughly tested under 'real life' conditions. In particular, at present, they have been used only with file collections under Linux (ext4) and Windows (NTFS) and may not yet work properly with MacOS X.* 

## Special warning for Windows users

Windows has a [maximum path length limitation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation), limiting the total length of a path to a file to 260 characters. This can cause problems for data-sets in which files with long names are stored in a deep hierarchy of sub-directories. In that case, the scripts for data management may crash, citing that some file could not be found, even though it is there when you look for it.

Starting from Windows 10, version 1607, the path length limitation has been removed, but you have to 'opt-in', which involves [editing the registry](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=powershell#enable-long-paths-in-windows-10-version-1607-and-later). For Windows 10 Pro, there is also a [GUI-guided procedure using the 'Group Policy Editor'](https://www.howtogeek.com/266621/how-to-make-windows-10-accept-file-paths-over-260-characters/) to remove the maximum path length limitation.

Based on current information (Summer 2026), this feature also affects Windows 11, requiring specific 'opt-in' action to remove the 260-character limit and enable long paths.


