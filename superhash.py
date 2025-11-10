#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# REMARK: In view of the cross-platform nature of this tool, it is necessary
#         to explicitly specify 'utf-8' as the encoding of files, else
#         Python will use the platform-specific encoding

__version__ = '0.1a2'  # For now, the version number represents the version of the data-format.

CHUNKSIZE = 67108864 # 64 MiB size, for hashing in chunks

import sys
import os
import os.path
import argparse
from pathlib import Path
import hashlib
from datetime import datetime
import csv

from tqdm import tqdm

cli = argparse.ArgumentParser()
cli.add_argument("src_dir", type=str,
                 help="source directory to be scanned")
cli.add_argument('-n', '--nohash', action='store_true',
                 help='do not calculate hashes, only generate file info tree')
cli.add_argument("-o", "--outpath", type=str,
                 help="path or pathname of result file")
clargs = cli.parse_args()

print('')
print("This is MANBAMM's superhash - v"+__version__+\
      " - by M.H.V. Werts, 2022-2025")
print("")

dtn = datetime.now()

p_src = Path(clargs.src_dir)
if not p_src.is_dir():
    sys.exit("Specified source is not a directory.")
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
    writer.writerow(['# timestamp_iso',
                     'rel_path_posix',
                     'filename',
                     'mtime_iso',
                     'size',
                     'md5digest'])
    # sorts according to root, keeping the subdirs and files in sync
    walklist = sorted(list(os.walk(p_src_abs)))
    for root, subdirs, files in tqdm(walklist):
        checksums = []
        rootrelative = os.path.relpath(root, p_src_abs.parent)
        # enforce storing pathnames as posix
        rootrel_posix = Path(rootrelative).as_posix()
        # sort also the files inside each directory
        for file in tqdm(sorted(files), leave = False):
            filepath = Path(root, file)
            if (filepath.resolve() == p_result_abs):
                tqdm.write('... skipping result file itself ('\
                           +str(p_result)+')')
            else:
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
                timestamp_iso = datetime.now().isoformat()
                checksums.append([timestamp_iso,
                                  rootrel_posix,
                                  file,
                                  mtime_iso,
                                  fpsize,
                                  md5digest])
        writer.writerows(checksums)
print('')
print('')
