#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# superhash-check.py and superhash.py should ideally be same version.
# 
# There is not necessarily backward/forward compatibility
# of the data file format (yet!). Efforts should be made to ensure
# compatibility with files generated with older version. For now,
# not really an issue.
#
# 

__version__ = '0.1a3'

import argparse
from pathlib import PurePosixPath
from datetime import datetime
import csv

from tqdm import tqdm

#%% classes and functions

DROPPATHPARTS = 1 # Number of intial parts of the path to drop (ideally, 1)

class SuperhashIndex:
    def __init__(self, fpn):
        with open(fpn, 'r', encoding='utf-8') as fin:
            rdr = csv.reader(fin, delimiter='\t', quoting=csv.QUOTE_NONE)
            self.header = [rdr.__next__() for i in range(5)]
            if not (self.header[0][0] == '# superhash-version'):
                raise Exception('Not a superhash file')
            if not (self.header[0][1] == __version__):
                print('*** WARNING! File generated with a different version of superhash ***')
                print('    File generated with v'+self.header[0][1]+', current software v'+__version__)
            self.lines = []
            for rawln in rdr:
                cleanpath = PurePosixPath(*PurePosixPath(\
                                               rawln[1]).parts[DROPPATHPARTS:])
                ln = [datetime.fromisoformat(rawln[0]),
                      cleanpath,
                      rawln[2],
                      datetime.fromisoformat(rawln[3]),
                      int(rawln[4]),
                      rawln[5]]
                self.lines.append(ln)
        self.shfilename = fpn
        self.seqsrchix = 0
        self.Nlines = len(self.lines)
                
    def print_stats(self):
        totalbytes = 0
        for ln in self.lines:
            totalbytes += ln[4]
        td = self.lines[-1][0] - self.lines[0][0]
        totaltime = td.total_seconds()
        throughp = totalbytes/(1e6*totaltime)
        print('Superhash file   :', self.shfilename)
        print('Generated on     :', self.header[1][1])
        print('Source directory :', self.header[2][1][:50])
        print('Total indexed    : {0:d} files'.format(self.Nlines))
        print('Total scanned    : {1:.3f} GB ({0:d} bytes)'.format(totalbytes,
                                                               totalbytes/1e9))
        print('Time taken       : {0:.1f} s'.format(totaltime))
        print('Throughput       : {0:.3f} MB/s'.format(throughp))
        print('')
        
    def seqsearch(self, path, fname):
        """
        Search for the line containing info for path, fname

        Parameters
        ----------
        path : pathlib.PurePath
            Path to be found.
        fname : str
            Filename to be found.

        Returns
        -------
        foundix : int or None
            Index of the line containing info for path, fname.
            Returns None if not found
            
        This implements a sequential search, which restarts at the last line
        after the line where a successful match was found. This makes subsequent
        searches highly efficient, since both SuperhashIndexes (superhash files)
        are expected to be 'in sync' over extended portions, even completely
        'in sync', thanks to sorting the os.walk() stuff.
        """
        foundix = None
        ix = self.seqsrchix
        while True:
            if fname == self.lines[ix][2]:
                if path.is_relative_to(self.lines[ix][1]):
                    foundix = ix
            ix += 1
            if (ix == self.Nlines):
                ix = 0
            if ix == self.seqsrchix:
                break
            if foundix is not None:
                break
        self.seqsrchix = ix
        return foundix
            

        

#%% main program

cli = argparse.ArgumentParser()
cli.add_argument("file1", type=str,
                 help="first superhash file")
cli.add_argument("file2", type=str,
                 help="2nd superhash file")
cli.add_argument("-m", "--missing", type=str,
                 help="file to write the list of missing entries to")
clargs = cli.parse_args()



print('')
print("MANBAMM's superhash-check - v"+__version__+" - by M.H.V. Werts, 2022-2025")
print("")

print('FILE #1')
print('=======')
sh1 = SuperhashIndex(clargs.file1)
sh1.print_stats()

print('FILE #2')
print('=======')
sh2 = SuperhashIndex(clargs.file2)
sh2.print_stats()

# search the lines present in sh2 in sh1, and compare MD5 checksums

print('Check data lines in File #2 against File #1')
print('===========================================')

if clargs.missing is None:
    dump_missing = False
else:
    dump_missing = True
    fmiss = open(clargs.missing, 'w', encoding='utf-8')
    wrtmiss = csv.writer(fmiss, delimiter='\t', lineterminator='\n',
                         quoting=csv.QUOTE_NONE)

lmissing = []
Nerrorsum = 0
for ln in tqdm(sh2.lines):
    rix = sh1.seqsearch(ln[1], ln[2])
    if rix is not None:
        if not ln[5] == sh1.lines[rix][5]:
            tqdm.write('MD5 checksum error: line {0:10d} "{1:s}"'.\
                       format(rix, ln[2]))
            Nerrorsum += 1
    else:
        lmissing.append([ln[0].isoformat(),
                         ln[1].as_posix(),
                         ln[2],
                         ln[3].isoformat(),
                         ln[4],
                         ln[5]])
Nnotfound = len(lmissing)
if dump_missing:
    wrtmiss.writerows(lmissing)
    fmiss.close()

print('')
print()
print('RESULT')
print('======')

if (Nnotfound > 0):
    print('Not found : {0:d} files (entries present in File#2 but not in File#1)'.\
          format(Nnotfound))
    if not dump_missing:
        print('            (If you want to generate a file with a list of the')
        print('            missing files, use the -m option).')
else:
    print('All entries in File#2 are present in File#1. Good!')
    
if (Nerrorsum > 0):    
    print('ERRORS    : {0:d} files (MD5 checksums disagree)'.format(Nerrorsum))
else:
    print('All MD5 checksums are good! No errors detected.')

print('')
print('')
