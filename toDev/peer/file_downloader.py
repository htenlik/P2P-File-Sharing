import socket, threading
from pathlib import Path
from common.protocol import Protocol


def _download_part(idx: int, peer_port: int, filename, dest_path: Path,
                   provider_ip: str, provider_port: int,
                   start_b: int, end_b: int, repo_dir: Path, results: list[bool]):
    size = end_b - start_b + 1
    s = socket.socket()
    s.settimeout(2.0)
    try:
        s.connect((provider_ip, provider_port))
    except Exception as e:
        print(f"PEER{peer_port} ConnectionFault Provider-> {provider_ip}:{provider_port} -> {e}")
        s.close()
        results[idx] = False
        return
    try:
        Protocol.start_download(s, filename, start_b, end_b)
        remaining, received = size, 0
        with open(dest_path, "r+b") as f:
            f.seek(start_b)
            while remaining > 0:
                chunk = s.recv(min(65536, remaining))
                if not chunk: break
                f.write(chunk)
                received += len(chunk)
                remaining -= len(chunk)
        s.close()
        append_peer_log(repo_dir, filename, f"{provider_ip}:{provider_port}")
        print(f"PEER{peer_port} {filename} part [{start_b}-{end_b}] downloaded from {provider_ip}:{provider_port}")
        results[idx] = True
    except Exception as e:
        print(f"PEER{peer_port} HATA: {filename} part [{start_b}-{end_b}] {provider_ip}:{provider_port} -> {e}")
        results[idx] = False


def parallel_download(server_ip, server_port, peer_port, repo_dir: Path, filename: str, size: int):
    s = socket.socket()
    try:
        s.connect((server_ip, server_port))
        Protocol.start_search(s, filename)
        response = Protocol.receive_msg(s)
    finally:
        s.close()

    providers = []
    tokens = response.split()
    if tokens[:2] == ["START", "PROVIDERS"]:
        for t in tokens[2:-1]:
            ip, p = t.split(":")
            providers.append((ip, int(p)))
    if not providers:
        print(f"PEER{peer_port} no provider found for {filename}.")
        return False

    # pre-allocate
    dest = Path(repo_dir) / filename
    with open(dest, "wb") as f:
        f.truncate(size)

    ranges = partition_ranges(size, len(providers))
    results = [False] * len(ranges)
    threads = []
    for idx, (provider, byte_range) in enumerate(zip(providers, ranges)):
        ip, p = provider
        start_b, end_b = byte_range
        t = threading.Thread(
            target=_download_part,
            args=(idx, peer_port, filename, dest, ip, p, start_b, end_b, Path(repo_dir), results),
            daemon=True,
        )
        t.start(); threads.append(t)
    for t in threads: t.join()
    all_parts_downloaded_successfully = all(results)
    if all_parts_downloaded_successfully:
        print(f"PEER{peer_port} {filename} has been downloaded.")
        s2 = socket.socket()
        try:
            s2.connect((server_ip, server_port))
            Protocol.start_providing(s2, peer_port, [filename])
        except Exception as e:
            print(f"PEER{peer_port} PROVIDING error: {e}")
        finally:
            s2.close()
    else:
        print(
            f"PEER{peer_port} DOWNLOAD FAILED: {filename}.")

    return all_parts_downloaded_successfully


def partition_ranges(total_size: int, k: int):
    base = total_size // k
    ranges = []
    start = 0
    for _ in range(k - 1):
        end = start + base - 1
        ranges.append((start, end))
        start = end + 1
    ranges.append((start, start + base + (total_size % k) - 1))
    return ranges

def append_peer_log(repo_dir: Path, filename: str, ip_port: str):
    with open(repo_dir.parent / "download.log", "a", encoding="utf-8") as f:
        f.write(f"{filename} {ip_port}\n")