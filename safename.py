#!/usr/bin/env python3
r"""
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

__version__ = '0.2'

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
    problem_detected = False
    fixed1problem = False
    pp = Path(root, fdn)

    #
    # 1. UNPRINTABLE check
    #
    # Check for presence of character with ASCII/Unicode code below 32
    # (unprintable characters). This is a dangerous problem and should be 
    # dealt with manually before using `safename`.
    # Thus, we will crash the program.
    # (unless we LIVEDANGEROUSLY = True)
    
    below32 = True in [ord(c)<32 for c in fdn]
    if below32 and not LIVEDANGEROUSLY:
        sys.exit("FATAL: illegal character in " + repr(str(pp)))
    else:
        # living dangerously
        if below32:
            problem_detected = True
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
        problem_detected = True
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
        problem_detected = True
        print('BADCHARS\t'+str(pp)+'\t'+dftype)
        if fixit and not fixed1problem:
            fixed1problem = True
            goodpp = Path(root, goodname)
            repair(pp, goodpp)

    #
    # 4. SYMLINKS check
    # 
    if pp.is_symlink():
        problem_detected = True
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
                    with open(goodpp, 'w', encoding='utf-8') as f1:
                        f1.write(str(pp.resolve()))
                    pp.unlink()
                    print('FIXED...')
                    print()
                    
    return ((not problem_detected), fixed1problem)



def scan(root_dir, repair_mode):
    """Walk the tree. Returns (N_unclean, stopped_early)."""
    n_unclean = 0
    for root, subdirs, files in sorted(os.walk(root_dir), reverse=True):
        entries = [(d, 'DIR') for d in sorted(subdirs)] + \
                  [(f, 'FILE') for f in sorted(files)]
        for name, dftype in entries:
            clean, fixed_pb = checkcheck(root, name, dftype, fixit=repair_mode)
            if not clean:
                n_unclean += 1
            if fixed_pb:
                return n_unclean, True   # leaves all loops at once
    return n_unclean, False          
        
        
#%% main code

cli = argparse.ArgumentParser(
    description = """
Check for compatibility problems in the names of files in a directory tree.
    
WARNING: with the -r / --repair option activated, this script may
         irreversibly alter the contents of your directory tree.
    """,
    
    formatter_class = argparse.RawDescriptionHelpFormatter,
    
    epilog = r"""
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

N_unclean, stopped_early = scan(p_src_abs, clargs.repair)

print('------------------------------------')
if stopped_early:
    print('safename terminated early: it fixed exactly 1 problem on 1 file.')
    print('Run it again to continue.')
elif N_unclean == 0:
    print('All scanned entries were found to be clean. Good!')
else:
    print(f'{N_unclean} unclean entries were found. These may need fixing.')
    

