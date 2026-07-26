import argparse
from pathlib import Path

DEFAULT_FILECOUNT_THRESH = 50
DEFAULT_FILESIZE_THRESH = 10_000_000

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

        # Update progress
        print(f"Scanning {total_dirs} directories: {i}/{total_dirs}", end="\r")

    print()  # Newline after progress is done
    return qualifying_dirs

parser = argparse.ArgumentParser(description="Identify directories with large numbers of files. Then check file sizes and nested subdirectories.")
parser.add_argument("directory", type=str, help="Root directory to scan")
parser.add_argument("--file-count-threshold",
                    type=int, default=DEFAULT_FILECOUNT_THRESH,
                    help=f"Minimum file count threshold (default: {DEFAULT_FILECOUNT_THRESH:d})")
parser.add_argument("--file-size-threshold",
                    type=int, default=DEFAULT_FILESIZE_THRESH,
                    help=f"File size threshold in bytes (default: {DEFAULT_FILESIZE_THRESH:,} bytes)")
args = parser.parse_args()

root = Path(args.directory)
if not root.exists():
    print(f"Error: Directory '{args.directory}' does not exist.")
    exit(1)

file_count_threshold = args.file_count_threshold
file_size_threshold = args.file_size_threshold

qualifying_dirs = scan_directory(root, file_count_threshold, file_size_threshold)

# Category 1: Fully qualifying directories
print("\n=== Fully Qualifying Directories ===")
fully_qualifying = [
    d for d in qualifying_dirs
    if d["largest_file_size"] <= file_size_threshold and not d["has_subdirs"]
]
for d in fully_qualifying:
    print(d["path"])

# Category 2: Directories with large files
print("\n=== Potentially Qualifying Directories with Large Files ===")
large_files = [
    d for d in qualifying_dirs
    if d["largest_file_size"] > file_size_threshold
]
for d in large_files:
    print(f"WARNING (contains large files):\t{d['path']}")

# Category 3: Directories with subdirectories
print("\n=== Potentially Qualifying Directories with Subdirectories ===")
with_subdirs = [
    d for d in qualifying_dirs
    if d["has_subdirs"]
]
for d in with_subdirs:
    print(f"WARNING (contains subdirectories):\t{d['path']}")
