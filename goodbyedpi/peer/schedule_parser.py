from pathlib import Path

def read_schedule(path: Path):
    waits_ms = 0
    jobs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t: continue
            if t.lower().startswith("wait"):
                parts = t.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    waits_ms = int(parts[1])
            else:
                if ":" in t:
                    name, size_str = t.split(":", 1)
                    jobs.append((name.strip(), int(size_str)))
    return waits_ms, jobs
