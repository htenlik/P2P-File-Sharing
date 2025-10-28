from pathlib import Path

def append_peer_log(repo_dir: Path, filename: str, ip_port: str):
    with open(repo_dir.parent / "peer.log", "a", encoding="utf-8") as f:
        f.write(f"{filename} {ip_port}\n")
