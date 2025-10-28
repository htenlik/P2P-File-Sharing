from pathlib import Path

def partition_ranges(total_size: int, k: int):
    base = total_size // k
    rem  = total_size %  k
    ranges, start = [], 0
    for i in range(k):
        part = base + (1 if i < rem else 0)
        end  = start + part - 1
        ranges.append((start, end))
        start = end + 1
    return ranges

def list_repo_files(repo_dir: Path):
    if not Path(repo_dir).exists():
        return []
    return [p.name for p in Path(repo_dir).iterdir() if p.is_file()]
