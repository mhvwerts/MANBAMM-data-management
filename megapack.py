"""
megapack.py

*** EXPERIMENTAL SCRIPT - USE AT YOUR OWN RISK ***

This script scans a directory tree, identifies directories containing
large numbers of small files, and compresses them into ZIP archives -
moving the originals to a backup location, or (once fully validated)
deleting them outright.

This is still under active testing. It has not been battle-tested
against a wide variety of real-world directory structures, filesystems,
or failure modes. Source-directory deletion is currently disabled
(NotImplementedError) until the compress/verify path has seen more
real-world use. Always test with --dry-run and/or --backup-dir first,
and never point this at data you don't have a separate backup of.
"""

import argparse
import shutil
import zipfile
from pathlib import Path

DEFAULT_FILECOUNT_THRESH = 40
DEFAULT_FILESIZE_THRESH = 12_000_000


def compress_directory(dir_path, zip_path, manifest=False):
    """Pack a directory into a store-only ZIP file (without data 
    compression).

    Assumes dir_path contains only files (no subdirectories) - the
    caller is responsible for filtering out any nested directories
    beforehand.

    If manifest is True, also write a tab-delimited manifest file
    (same name as zip_path, with '.manifest.txt' as suffix) listing
    each archived file's name, byte offset, size, and CRC-32.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
        for file in dir_path.iterdir():
            if file.is_file():
                zipf.write(file, arcname=file.name)

        if manifest:
            manifest_path = zip_path.with_suffix('.manifest.txt')
            with manifest_path.open('w') as f:
                f.write("filename\tbyte_offset\tfile_size\tcrc32\n")
                for info in zipf.infolist():
                    f.write(
                        f"{info.filename}\t{info.header_offset}\t"
                        f"{info.file_size}\t{info.CRC:08x}\n"
                    )


def scan_directory(root, file_count_threshold):
    qualifying_dirs = []

    print("Counting directories...")
    all_dirs = [d for d in root.rglob('*') if d.is_dir()]
    total_dirs = len(all_dirs)
    print(f"Scanning {total_dirs} directories: 0/{total_dirs}", end="\r")

    for i, dir_path in enumerate(all_dirs, 1):
        files = [f for f in dir_path.iterdir() if f.is_file()]
        subdirs = [d for d in dir_path.iterdir() if d.is_dir()]

        if len(files) > file_count_threshold:
            largest_file_size = max(f.stat().st_size for f in files) if files else 0
            has_subdirs = len(subdirs) > 0
            qualifying_dirs.append({
                "path": str(dir_path),
                "file_count": len(files),
                "largest_file_size": largest_file_size,
                "has_subdirs": has_subdirs,
            })

        print(f"Scanning {total_dirs} directories: {i}/{total_dirs}", end="\r")

    print()  # Newline after progress
    return qualifying_dirs
    

def main():
    parser = argparse.ArgumentParser(description="Identify directories with large numbers of small files and pack them into ZIP files without compression.")
    parser.add_argument("directory", type=str, help="Root directory to scan")
    parser.add_argument("--file-count-threshold", type=int, default=DEFAULT_FILECOUNT_THRESH,
                        help=f"Minimum file count threshold (default: {DEFAULT_FILECOUNT_THRESH:d})")
    parser.add_argument("--file-size-threshold", type=int, default=DEFAULT_FILESIZE_THRESH,
                        help=f"File size threshold in bytes (default: {DEFAULT_FILESIZE_THRESH:,} bytes)")
    parser.add_argument("--backup-dir", type=str, default=None,
                        help="Backup directory to which processed directories are moved (default: None, will delete sources)")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Simulate actions without applying changes (default: False)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute actions (default: False, requires confirmation)")
    parser.add_argument("--scan-only", action="store_true", default=False,
                        help="Only scan the directory tree (default: False)")
    parser.add_argument("--zip-overwrite", action="store_true", default=False,
                        help="Overwrite a pre-existing target zip instead of skipping the directory "
                             "(default: False). Useful to retry a directory whose zip was left "
                             "incomplete/corrupt by an interrupted (e.g. Ctrl-C) or failed previous run.")
    args = parser.parse_args()

    print("*" * 60)
    print("megapack.py - EXPERIMENTAL SCRIPT - USE AT YOUR OWN RISK")
    print("This tool can compress, move, and (in future) delete real")
    print("directories. It has not been fully validated. Make sure you")
    print("have independent backups before running with --execute.")
    print("*" * 60)
    print()

    root = Path(args.directory)
    if not root.exists():
        print(f"Error: Directory '{args.directory}' does not exist.")
        exit(1)

    backup_root = Path(args.backup_dir) if args.backup_dir else None
    if backup_root and not backup_root.exists():
        print(f"Error: Backup directory '{args.backup_dir}' does not exist.")
        exit(1)

    file_count_threshold = args.file_count_threshold
    file_size_threshold = args.file_size_threshold
    dry_run = args.dry_run
    execute = args.execute
    scan_only = args.scan_only
    zip_overwrite = args.zip_overwrite

    qualifying_dirs = scan_directory(root, file_count_threshold)

    # Category 2: Directories with large files
    print("\n=== Potentially qualifying directories with large files ===")
    large_files = [
        d for d in qualifying_dirs
        if d["largest_file_size"] > file_size_threshold
        ]
    for d in large_files:
        print(f"WARNING (large files):\t{d['path']}")

    # Category 3: Directories with subdirectories
    print()
    print("\n=== Potentially qualifying directories with subdirectories ===")
    with_subdirs = [
        d for d in qualifying_dirs
        if d["has_subdirs"]
        ]
    for d in with_subdirs:
        print(f"WARNING (subdirectories):\t{d['path']}")

    # Category 1: Fully qualifying directories
    print()
    print("\n=== Fully qualifying directories to be processed ===")
    fully_qualifying = [
        d for d in qualifying_dirs
        if d["largest_file_size"] <= file_size_threshold and not d["has_subdirs"]
        ] 
    
    if not fully_qualifying:
        print("*** No fully qualifying directories! Nothing to process...")
        print()
        return
    else:
        for d in fully_qualifying:
            print(d["path"])

    if not scan_only:
        # Simulate or perform actions
        print("\n=== Actions to Perform ===")
        for d in fully_qualifying:
            dir_path = Path(d["path"])
            zip_path = dir_path.parent / (dir_path.name + '.zip')

            if dry_run:
                print(f"[DRY RUN] Compress {dir_path} -> {zip_path}")
                if backup_root:
                    backup_path = backup_root / dir_path.relative_to(root)
                    print(f"[DRY RUN] Move {dir_path} -> {backup_path}")
                else:
                    print(f"[DRY RUN] Delete {dir_path}")
            else:
                print(f"Compress {dir_path} -> {zip_path}")
                print(f"Move {dir_path} -> {backup_root / dir_path.relative_to(root)}" if backup_root else f"Delete {dir_path}")

        if not dry_run:
            if execute:
                confirm = input("\nProceed as planned? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("Mission aborted.")
                    return
                print()
                for d in fully_qualifying:
                    dir_path = Path(d["path"])
                    zip_path = dir_path.parent / (dir_path.name + '.zip')

                    if zip_path.exists():
                        if zip_overwrite:
                            print(f"Overwriting existing zip {zip_path}")
                        else:
                            print(f"SKIPPING (no '--zip-overwrite'). Target zip already exists: {dir_path} -> {zip_path}")
                            continue
                        
                    print(f"Zipping to {zip_path}")
                    compress_directory(dir_path, zip_path, manifest=True)
                    
                    # Verify integrity before destroying the original.
                    # On failure we raise rather than skip: the corrupt zip is left
                    # behind next to the intact source directory. Remove the zip
                    # manually before re-running, or the next run will treat it as
                    # already-processed and skip the directory with a
                    # "target zip already exists" message.
                    with zipfile.ZipFile(zip_path) as zf:
                        bad_file = zf.testzip()
                        original_file_count = sum(1 for f in dir_path.rglob('*') if f.is_file())
                        if bad_file or len(zf.namelist()) != original_file_count:
                            raise RuntimeError(
                                f"Verification failed for {zip_path} (source: {dir_path}). "
                                f"The source directory was left untouched. Delete the corrupt "
                                f"zip before re-running, or it will be skipped as already-processed."
                            )
                    print('Zip OK')
                    
                    if backup_root:
                        backup_path = backup_root / dir_path.relative_to(root)
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(dir_path), str(backup_path))
                        print(f"Moved {dir_path} -> {backup_path}")
                    else:
                        raise NotImplementedError("Please supply a '--backup-dir'. Source directory deletion will only be implemented when code sufficiently stress-tested in real-life situations.")
                        # shutil.rmtree(dir_path)
                        # print(f"Deleted {dir_path}")
            else:
                print()
                print(60*'*')
                print("Plans aborted! If you really want to proceed, please supply the '--execute' flag on the command line")
                print(60*'*')

if __name__ == "__main__":
    main()
    
    
