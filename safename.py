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

__version__ = '0.1a2'

import sys
import os
import argparse
from pathlib import Path

LIVEDANGEROUSLY = False # If True, will also work with filenames containing
                        # characters with codepoints under 32 (non-printable)
KILLSYMLINKS = False    # If True, will convert symlinks to text files
                        # containing full target pathname

#%% classes and functions

def repair(badpp, goodpp):
    print('FIXING\t*************')
    print('FIXING\t*** bad name:')
    print('FIXING\t',str(badpp))
    print('FIXING\t*************')
    print('FIXING\t*** good name:')
    print('FIXING\t',str(goodpp))
    print('FIXING\t*************')
    if goodpp.exists():
        print('FIXING\tTARGET NAME ALREADY EXISTS. Not going ahead.')
        print('NOT FIXED...')
        print()
    else:
        print('FIXING\tTarget name does not exist. Going ahead.')
        print('FIXED...')
        print()
        badpp.rename(goodpp)


def checkcheck(root, fdn, dftype, fixit = False):
    """
    Check for compatibility problems of an entry in the directory tree.
    
    Can also fix these problems. FIXES ONLY ONE PROBLEM AT A TIME! 
    Else problems are expected. Use multiple runs to fix files displaying
    several problems at the same time (e.g. SYMLINK with BADCHARS)

    Parameters
    ----------
    root : str
        Path leading to entry (file/directory).
    fdn : str
        Name of sub-directory or file.
    dftype : str
        Information (FILE/DIR) to be printed in third column of output.
    fixit : boolean, optional
        Fix problems (ONE AT A TIME!!). The default is False.

    Returns
    -------
    None.

    """
    fixed1problem = False
    pp = Path(root, fdn)

    #
    # 1. UNPRINTABLE check
    #
    # Check for presence of character with ASCII/Unicode code below 32
    # (unprintable characters). This is a dangerous problem and should be 
    # dealt with manually before using `safename`.
    # Thus, we will raise an AssertionError and crash the program.
    # (unless we LIVEDANGEROUSLY = True)
    
    below32 = True in [ord(c)<32 for c in fdn]
    if not LIVEDANGEROUSLY:
        assert not below32, "FATAL: illegal character in "+str(pp)
    else:
        # living dangerously
        if below32:
            print('UNPRINTABLE\t'+str(pp)+'\t'+dftype)
            if fixit and not fixed1problem:
                fixed1problem = True
                # create new name, simply skipping all unprintable characters
                goodname = ''
                for c in fdn:
                    if ord(c)<32:
                        pass
                    else:
                        goodname += c
                goodpp = Path(root, goodname)
                repair(pp, goodpp)

     
    #
    # 2. WHITESPACE check
    #
    goodname = fdn.strip()
    if goodname != fdn:
        print('WHITESPACE\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            goodpp = Path(root, goodname)
            repair(pp, goodpp)
            
    #
    # 3. BADCHARS check
    # 
    # backslash, use r'string'
    fixchars = str.maketrans(r'<>:"/\|?*', r"[]-'____x")
    goodname = fdn.translate(fixchars)
    if goodname != fdn:
        print('BADCHARS\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            goodpp = Path(root, goodname)
            repair(pp, goodpp)

    #
    # 4. SYMLINKS check
    # 
    if pp.is_symlink():
        print('SYMLINK\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            print('FIXING\t*************')
            print('FIXING\t*** symlink:')
            print('FIXING\t', str(pp))
            print('FIXING\t*** resolves to:')
            print('FIXING\t', str(pp.resolve()))
            print('FIXING\t*************')
            if not KILLSYMLINKS:
                print('FIXING\t!! DOING NOTHING - set KILLSYMLINKS to kill and'\
                    ' transform symlinks')
                print('NOT FIXED\t*************')
            else:
                goodname = 'SYMLINK_'+fdn
                print('FIXING\t*** symlink memorial text file')
                print('FIXING\t', goodname)
                goodpp = Path(root, goodname)
                if goodpp.exists():
                    print('FIXING\tTARGET NAME ALREADY EXISTS')
                    print('NOT FIXED...')
                    print()
                else:
                    print('FIX\tTarget name does not exist. Going ahead.')
                    with open(goodpp, 'w') as f1:
                        f1.write(str(pp.resolve()))
                    pp.unlink()
                    print('FIXED...')
                    print()
                
        
        
#%% main code

cli = argparse.ArgumentParser(
    description = """
Check for compatibility problems in the names of files in a directory tree.
    
WARNING: with the -r / --repair option activated, this script may
         irreversibly alter the contents of your directory tree.
    """,
    
    formatter_class = argparse.RawDescriptionHelpFormatter,
    
    epilog =      
    """
safename currently identifies four types of problems:
    1. Presence of 'non-printable' characters in names ('UNPRINTABLE'). Fatal
       error.
    2. Leading or trailing whitespace (*e.g.*, spaces) in a pathname 
       ('WHITESPACE')
    3. Presence of characters  `< > : " / \ | ? *` ('BADCHARS')
    4. Symbolic links ('SYMLINK')
    """)
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

