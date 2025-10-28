import socket, threading, time
from pathlib import Path
from common.logger import append_peer_log
from common.protocol import send_cmd
from common.utils import partition_ranges

def _download_part(banner, filename, dest_path: Path,
                   provider_ip: str, provider_port: int,
                   start_b: int, end_b: int, repo_dir: Path, results: dict):
    size = end_b - start_b + 1
    last_err, s = None, None
    for _ in range(8):
        try:
            s = socket.socket(); s.settimeout(2.0)
            s.connect((provider_ip, provider_port)); break
        except Exception as e:
            last_err = e; time.sleep(0.5)
    if s is None:
        print(f"{banner} HATA: {filename} [{start_b}-{end_b}] {provider_ip}:{provider_port} -> {last_err}")
        results[(start_b, end_b)] = False; return
    try:
        s.sendall((f"START DOWNLOAD {filename} {start_b} {end_b} END").encode())
        remaining, received = size, 0
        with open(dest_path, "r+b") as out:
            out.seek(start_b)
            while remaining > 0:
                chunk = s.recv(min(65536, remaining))
                if not chunk: break
                out.write(chunk)
                received += len(chunk)
                remaining -= len(chunk)
        s.close()
        if received != size:
            print(f"{banner} UYARI: {filename} [{start_b}-{end_b}] eksik alındı ({received}/{size}) {provider_ip}:{provider_port}")
            results[(start_b, end_b)] = False; return
        append_peer_log(repo_dir, filename, f"{provider_ip}:{provider_port}")
        print(f"{banner} {filename} parça [{start_b}-{end_b}] indirildi {provider_ip}:{provider_port}")
        results[(start_b, end_b)] = True
    except Exception as e:
        print(f"{banner} HATA: {filename} parça [{start_b}-{end_b}] {provider_ip}:{provider_port} -> {e}")
        results[(start_b, end_b)] = False

def parallel_download(banner, server_ip, server_port, peer_port, repo_dir: Path, filename: str, size: int):
    # providerları sor
    resp = send_cmd(server_ip, server_port, f"START SEARCH {filename}")
    providers = []
    toks = resp.split()
    if toks[:2] == ["START", "PROVIDERS"]:
        for t in toks[2:-1]:
            if ":" in t:
                ip, p = t.split(":")
                try: providers.append((ip, int(p)))
                except: pass
    providers = [(ip, p) for (ip, p) in providers if p != peer_port]
    if not providers:
        print(f"{banner} {filename} bulunamadı veya sağlayıcılar hazır değil!")
        return False

    # pre-allocate
    dest = Path(repo_dir) / filename
    with open(dest, "wb") as f:
        if size > 0: f.truncate(size)

    ranges = partition_ranges(size, len(providers))
    results, threads = {}, []
    for (prov, rng) in zip(providers, ranges):
        ip, p = prov; start_b, end_b = rng
        t = threading.Thread(target=_download_part,
                             args=(banner, filename, dest, ip, p, start_b, end_b, Path(repo_dir), results),
                             daemon=True)
        t.start(); threads.append(t)
    for t in threads: t.join()
    ok = all(results.get(r, False) for r in ranges)
    if ok:
        print(f"{banner} {filename} indirildi.")
        try: send_cmd(server_ip, server_port, f"START PROVIDING {peer_port} 1 {filename}")
        except Exception as e:
            print(f"{banner} PROVIDING (tekil) hatası: {e}")
    else:
        print(f"{banner} İNDİRME BAŞARISIZ: {filename}. Dosya eksik/bozuk olabilir, PROVIDING yapılmadı.")
    return ok
