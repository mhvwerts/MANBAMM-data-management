import argparse
# import shutil
# import zipfile
from pathlib import Path

DEFAULT_FILECOUNT_THRESH = 50
DEFAULT_FILESIZE_THRESH = 10_000_000

def compress_directory(dir_path, zip_path):
    """Compress a directory into a ZIP file."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in dir_path.rglob('*'):
            if file.is_file():
                zipf.write(file, arcname=file.relative_to(dir_path))

def scan_directory(root, file_count_threshold, file_size_threshold):
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
    parser = argparse.ArgumentParser(description="Identify and compress directories with large numbers of small files.")
    parser.add_argument("directory", type=str, help="Root directory to scan")
    parser.add_argument("--file-count-threshold", type=int, default=DEFAULT_FILECOUNT_THRESH,
                        help=f"Minimum file count threshold (default: {DEFAULT_FILECOUNT_THRESH:d})")
    parser.add_argument("--file-size-threshold", type=int, default=DEFAULT_FILESIZE_THRESH,
                        help=f"File size threshold in bytes (default: {DEFAULT_FILESIZE_THRESH:,} bytes)")
    parser.add_argument("--backup-dir", type=str, default=None,
                        help="Backup directory to move processed directories to (default: None, will delete)")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Simulate actions without making changes (default: False)")
    # TODO: add execute flag
    args = parser.parse_args()

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
    execute = False # TODO: add execute flag argument to parser (see TODO above)

    qualifying_dirs = scan_directory(root, file_count_threshold, file_size_threshold)

    # Category 1: Fully qualifying directories
    print("\n=== Fully Qualifying Directories ===")
    fully_qualifying = [
        d for d in qualifying_dirs
        if d["largest_file_size"] <= file_size_threshold and not d["has_subdirs"]
    ]
    for d in fully_qualifying:
        print(d["path"])

    if not fully_qualifying:
        print("No directories to process.")
        return

    # Simulate or perform actions
    print("\n=== Actions to Perform ===")
    for d in fully_qualifying:
        dir_path = Path(d["path"])
        zip_path = dir_path.with_suffix('.zip')

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
            confirm = input("\nProceed with changes? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                return

            for d in fully_qualifying:
                dir_path = Path(d["path"])
                zip_path = dir_path.with_suffix('.zip')
                compress_directory(dir_path, zip_path)
                if backup_root:
                    backup_path = backup_root / dir_path.relative_to(root)
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dir_path), str(backup_path))
                    print(f"Moved {dir_path} -> {backup_path}")
                else:
                    shutil.rmtree(dir_path)
                    print(f"Deleted {dir_path}")
        else:
            print()
            print(60*'*')
            print("Plans aborted! If you really want to proceed, please supply the '--execute' flag on the command line")
            print(60*'*')

if __name__ == "__main__":
    main()
    
    