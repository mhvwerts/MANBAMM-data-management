#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## safename: filenames that are compatible across Windows, MacOSX and Linux

Local copies of (parts of) the datafile collection can be stored on Windows, 
MacOSX, or Linux. The characters allowed in file and directory names are not
the same across these systems. We should therefore ensure that the names of
files and directories ('pathnames') have only characters that are compatible
with all systems. This can be done with the aid of `safename`.

`safename` currently identifies four types of problems:
1. presence of 'non-printable' characters in names ('UNPRINTABLE'). Fatal
   error.
2. leading or trailing whitespace (*e.g.*, spaces) in a pathname ('WHITESPACE')
3. presence of characters  `< > : " / \ | ? *` ('BADCHARS')
4. symbolic links ('SYMLINK')

TODO: sync the text above with `README.md`
"""

__version__ = '0.1a1'

import sys
import os
import argparse
from pathlib import Path

LIVEDANGEROUSLY = False # If True, will also work with filenames containing
                        # characters with codepoints under 32 (non-printable)

#%% classes and functions


def checkcheck(root, fdn, dftype, fixit = False):
    """
    Check for compatibility problems of an entry in the directory tree.
    
    TODO: also fix problems, but ONLY FIX ONE PROBLEM AT A TIME!!!!
    Problem resolution order should be WHITESPACE, BADCHARS, SYMLINK

    Parameters
    ----------
    root : str
        Path leading to entry (file/directory).
    fdn : str
        Name of sub-directory or file.
    dftype : str
        Information (FILE/DIR) to be printed in third column of output.
    fixit : TYPE, optional
        Fix problems (ONE AT A TIME!!). The default is False.

    Returns
    -------
    None.

    """
    fixed1problem = False
    pp = Path(root, fdn)

    # Check for presence of character with ASCII/Unicode code below 32
    # (unprintable characters). This is a dangerous problem and should be 
    # dealt with manually before using `safename`
    below32 = True in [ord(c)<32 for c in fdn]
    if not LIVEDANGEROUSLY:
        assert not below32, "FATAL: illegal character in "+str(pp)
    else:
        # live dangerously
        if below32:
            print('UNPRINTABLE\t'+str(pp)+'\t'+dftype)
            if fixit and not fixed1problem:
                fixed1problem = True
                goodname = ''
                for c in fdn:
                    if ord(c)<32:
                        pass
                    else:
                        goodname += c
                goodpp = Path(root, goodname)
                print('FIX\t*************')
                print('FIX\t*** bad name:')
                print('FIX\t',str(pp))
                print('FIX\t*************')
                print('FIX\t*** good name:')
                print('FIX\t',str(goodpp))
                print('FIX\t*************')
                if goodpp.exists():
                    print('FIX\tTARGET NAME ALREADY EXISTS')
                else:
                    print('FIX\tTarget name does not exist. Go ahead.')
                print('FIX\t**************')
                pp.rename(goodpp)
   
    if fdn.strip() != fdn:
        print('WHITESPACE\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            print('FIX\t***FIX WHITESPACE*** TO DO...')

    # backslash, use r'string'
    #TODO: change algo -> create corrected version then compare with original
    # use .translate()
    containsForbidden = True in [c in fdn for c in r'<>:"/\|?*']
    if containsForbidden:
        print('BADCHARS\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            print('FIX\t***FIX BADCHARS*** TO DO...')

    if pp.is_symlink():
        print('SYMLINK\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            print('FIX\t***FIX SYMLINK*** TO DO...')
        
#%% main code

cli = argparse.ArgumentParser()
cli.add_argument("src_dir", type=str,
                 help="Source directory to be scanned.")
cli.add_argument('-r', '--repair', action='store_true',
                 help='Fix detected problems, ONE AT A TIME.')
clargs = cli.parse_args()

p_src = Path(clargs.src_dir)
if not p_src.is_dir():
    sys.exit("Specified source is not a directory.")
p_src_abs = p_src.resolve(strict=True)

print("MANBAMM's safename - v"+__version__)
print('------------------------------------')
print('Source directory:   ', str(p_src))
print('')

walklist = sorted(list(os.walk(p_src_abs)))
for root, subdirs, files in walklist:
    for subdir in sorted(subdirs):
        checkcheck(root, subdir, 'DIR', fixit=clargs.repair)
    for file in sorted(files):
        checkcheck(root, file, 'FILE', fixit=clargs.repair)

