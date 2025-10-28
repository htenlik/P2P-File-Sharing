from pathlib import Path

def preallocate(dest: Path, size: int):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        if size > 0:
            f.truncate(size)
