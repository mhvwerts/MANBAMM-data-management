#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# REMARK: In view of the cross-platform nature of this tool, it is necessary
#         to explicitly specify 'utf-8' as the encoding of files, else
#         Python will use the platform-specific encoding

__version__ = '0.2'  

CHUNKSIZE = 67108864 # 64 MiB size, for hashing in chunks

import sys
import os
import os.path
import argparse
from pathlib import Path
import hashlib
from datetime import datetime
import csv
import json

from tqdm import tqdm

cli = argparse.ArgumentParser()
cli.add_argument('-n', '--nohash', action='store_true',
                 help='do not calculate hashes, only generate file info tree')
cli.add_argument("-o", "--outpath", type=str,
                 help="path or pathname of result file")
cli.add_argument("-r", "--resume", type=str,
                 help="resume superhash based on existing file")
cli.add_argument("-s", "--src_dir", type=str,
                 help="source directory to be scanned")
clargs = cli.parse_args()

print('')
print("This is MANBAMM's superhash - v"+__version__+\
      " - by M.H.V. Werts, 2022-2026")
print("")

dtn = datetime.now()

if clargs.resume is not None:
    #
    # restart from existing, incomplete superhash data file
    #
    p_result = Path(clargs.resume)
    p_result_abs = p_result.resolve(strict=False)
   
    with open(p_result, 'r', encoding='utf-8') as fin:
        rdr = csv.reader(fin, delimiter='\t', quoting=csv.QUOTE_NONE)
        header = [rdr.__next__() for i in range(4)]
        if not (header[0][0] == '# superhash-version'):
            print(f'Error: not a superhash file "{clargs.resume}"')
            sys.exit(2)
        if not (header[0][1] == __version__):
            print('Error: File generated with a different version of superhash. Revise your script.', 
                  file=sys.stderr)
            print('       File generated with v'+header[0][1]+', current software v'+__version__,
                  file=sys.stderr)
            sys.exit(2)
        
        # This header line contains the absolute path as a posix string
        # Readily converted back to an actual path
        p_src_abs = Path(header[2][1])

        walklist = []
        
        line = fin.readline() # this is an empty '#' comment line
        line = fin.readline()
        assert line.strip() == "#BEGIN-WALKLIST-JSONL", "Ill-formatted input file. Cannot resume."
         
        for line in fin:
            stripped = line.rstrip("\n")
            if stripped == "#END-WALKLIST-JSONL":
                break
            assert stripped.startswith("#"), "malformed walklist line"
            dirpath, dirnames, filenames = json.loads(stripped[1:])
            walklist.append((dirpath, dirnames, filenames))
            
        line = fin.readline() # this is an empty '#' comment line
        line = fin.readline()
        assert line.strip() == "#BEGIN-SUPERHASH-TSV", "Ill-formatted input file. Cannot resume."
        line = fin.readline() # skip TSV header line
        
       
        print('Scanning for resume point...')

        # Here we use a cheap scanning mechanism: just compare file-names
        # This is not 100% without risk, but probably OK.
        # Worst case: we skip/rescan some files and may have problems
        # resuming again after a new interruption
        #TODO: give this some extra scrutiny
        # and perhaps add a check of the path (last few members)
        
        walkix = 0 # scan over walklist by index
        tsvendfound = False
        for root, subdirs, files in tqdm(walklist):
            fileix=0
            for file in tqdm(sorted(files), leave = False):
                try:
                    rawtsvln = rdr.__next__()
                except StopIteration:
                    tsvendfound = True
                    break
                if not file==rawtsvln[2]:
                    print(f'Error: incompatible file names: "{file}" "{rawtsvln[2]}" ')
                    sys.exit(2)
                fileix+=1
            if tsvendfound:
                break                    
            walkix+=1

        # remove files already processed from current walklist line
        walklist[walkix] = (walklist[walkix][0],
                            walklist[walkix][1],
                            walklist[walkix][2][fileix:])
        # keep only remaining files from walklist
        walklist = walklist[walkix:]

else:
    #
    # Start afresh. Create a fresh file, with a fresh header and a fresh
    # walklist.
    # 
    if clargs.src_dir is None:
        print("Error: Please supply a --src_dir", file=sys.stderr)
        sys.exit(2)
    p_src = Path(clargs.src_dir)
    if not p_src.is_dir():
        print("Error: Specified source is not a directory", file=sys.stderr)
        sys.exit(2)
    p_src_abs = p_src.resolve(strict=True)
    
    md5st = 'noMD5' if clargs.nohash else ''
    dts = dtn.strftime('%y%m%d_%H%M%S')
    result_file = p_src_abs.stem+"_sh"+dts+md5st+".tsv"
    if clargs.outpath is None:
        p_result = Path(result_file)
    else:
        p_out = Path(clargs.outpath)
        if p_out.is_dir():
            p_result = Path(p_out, result_file)
        else:
            result_file = clargs.outpath
            p_result = Path(result_file)
    
    p_result_abs = p_result.resolve(strict=False)
    
    print('Source directory:   ', str(p_src))
    print('Output file     :   ', str(p_result))
    print('')

    with open(p_result, 'w', encoding='utf-8') as fout:
        writer = csv.writer(fout, delimiter='\t', lineterminator='\n',
                            quoting=csv.QUOTE_NONE)
        writer.writerow(['# superhash-version', __version__])
        writer.writerow(['# superhash-start-timestamp-iso', dtn.isoformat()])
        writer.writerow(['# absolute-path-source-dir',p_src_abs.as_posix()])
        writer.writerow(['# absolute-path-superhash-file',p_result_abs.as_posix()])

        
        # Cold start 
        print('Preparing file list... please stand by...')
        
        # sorts according to root, keeping the subdirs and files in sync
        walklist = sorted(list(os.walk(p_src_abs)))
        
        # insert walklist as JSONL block into file to enable the restart of an 
        # aborted superhash scan
        fout.write("#\n")
        fout.write("#BEGIN-WALKLIST-JSONL\n")
        for dirpath, dirnames, filenames in walklist:
            line = json.dumps([dirpath, dirnames, filenames], ensure_ascii=False)
            fout.write("#" + line + "\n")
        fout.write("#END-WALKLIST-JSONL\n")
        fout.write("#\n")
         
        # start of actual TSV block
        fout.write("#BEGIN-SUPERHASH-TSV\n")
        writer.writerow(['# timestamp_iso',
                         'rel_path_posix',
                         'filename',
                         'mtime_iso',
                         'size',
                         'md5digest'])

print()
print('Done! Moving on...')
print()


# Reopen file in APPEND mode to write the TSV superhash lines
#  do not forget to re-instantiate the CSV writer
with open(p_result, 'a', encoding='utf-8') as fout:
    writer = csv.writer(fout, delimiter='\t', lineterminator='\n',
                        quoting=csv.QUOTE_NONE)
    for root, subdirs, files in tqdm(walklist):
        checksums = []
        rootrelative = os.path.relpath(root, p_src_abs.parent)
        # enforce storing pathnames as posix
        rootrel_posix = Path(rootrelative).as_posix()
        # sort also the files inside each directory
        for file in tqdm(sorted(files), leave = False):
            filepath = Path(root, file)
            if (filepath.resolve() == p_result_abs):
                # tqdm.write('... skipping result file itself ('\
                #            +str(p_result)+')')
                print("Error: The result file must not be inside the scanned directory tree.", file=sys.stderr)
                print("Tip:   Try renaming the result file in-place and restart. It will not be in the walklist anymore.", file=sys.stderr)
                sys.exit(2)
            else:
                timestamp_iso = datetime.now().isoformat()
                # Files might be gone between creation of walklist and actual
                # scan. Not a problem (if limited to a few files)
                #TODO: emit warning and/or set limit
                if filepath.exists():
                    fpstat = filepath.stat()
                    fpsize = fpstat.st_size
                    mtime_iso = datetime.fromtimestamp(fpstat.st_mtime).isoformat()
                    with open(filepath, 'rb') as _file:
                        if clargs.nohash:
                            md5digest = ''
                        else:
                            cumhash = hashlib.md5()
                            for chunk in iter(lambda: _file.read(CHUNKSIZE), b''):
                                cumhash.update(chunk)
                            md5digest = cumhash.hexdigest()
                else:
                    # insert place holder info
                    # keeping the file list in sync
                    mtime_iso = timestamp_iso 
                    fpsize = 0
                    md5digest = '!FILE_GONE'

                checksums.append([timestamp_iso,
                                  rootrel_posix,
                                  file,
                                  mtime_iso,
                                  fpsize,
                                  md5digest])
        writer.writerows(checksums)
        
    # Write end marker. The presence of this marker indicates that the
    # full tree was scanned and included in the superhash file.
    # If the marker is absent (v0.2 file format), this signifies that
    # the superhash data in the file is incomplete.
    #TODO: include this in 'superhash-check.py'
    fout.write("#END-SUPERHASH-TSV\n")
    fout.write("#\n")
print('')
print('')
