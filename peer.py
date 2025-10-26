# peer.py
import socket
import threading
import sys
import os
import time
from pathlib import Path

END = b" END"  # sunucunun kullandığı sonlandırıcı ile birebir aynı olmalı

# ---------- Yardımcılar ----------
def recv_until_end(sock: socket.socket) -> str:
    buf = b""
    while END not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf.decode().strip()

def send_cmd(ip: str, port: int, text: str) -> str:
    """Sunucuya tek seferlik komut yolla, cevabı END'e kadar oku."""
    s = socket.socket()
    s.connect((ip, port))
    s.sendall((text + " END").encode())
    reply = recv_until_end(s)
    s.close()
    return reply

def log_line(repo_dir: Path, filename: str, ip_port: str):
    """Her eklemede dosyayı aç-kapat (ödev koşulu)."""
    with open(repo_dir.parent / "peer.log", "a", encoding="utf-8") as f:
        f.write(f"{filename} {ip_port}\n")

def partition_ranges(total_size: int, k: int):
    """[start, end] inclusive aralıkları k parçaya böl."""
    # k sağlayıcıya olabildiğince eşit paylaştır
    base = total_size // k
    rem = total_size % k
    ranges = []
    start = 0
    for i in range(k):
        part = base + (1 if i < rem else 0)
        end = start + part - 1
        ranges.append((start, end))
        start = end + 1
    return ranges

def read_schedule(path: Path):
    """schedule dosyasını oku: ('wait', ms) ve (name, size) girdeleri döndür."""
    waits_ms = 0
    jobs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("wait"):
                # ör: wait 500
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    waits_ms = int(parts[1])
            else:
                # ör: a.dat:00104857600
                if ":" in line:
                    name, size_str = line.split(":", 1)
                    size = int(size_str)
                    jobs.append((name.strip(), size))
    return waits_ms, jobs

def list_repo_files(repo_dir: Path):
    """Repo içindeki mevcut dosya adlarını (sadece isim) döndür."""
    if not repo_dir.exists():
        return []
    names = []
    for p in repo_dir.iterdir():
        if p.is_file():
            names.append(p.name)
    return names

# ---------- Parça indirme işçisi ----------
def download_part(worker_id: int, filename: str, dest_path: Path,
                  provider_ip: str, provider_port: int,
                  start_b: int, end_b: int, log_repo_dir: Path, banner: str):
    size = end_b - start_b + 1
    try:
        s = socket.socket()
        s.connect((provider_ip, provider_port))
        cmd = f"START DOWNLOAD {filename} {start_b} {end_b}"
        s.sendall((cmd + " END").encode())
        # İkili veri geliyor; miktarı biliyoruz -> tam 'size' byte oku
        remaining = size
        with open(dest_path, "r+b") as out:
            out.seek(start_b)
            while remaining > 0:
                chunk = s.recv(min(65536, remaining))
                if not chunk:
                    break
                out.write(chunk)
                remaining -= len(chunk)
        s.close()
        log_line(log_repo_dir, filename, f"{provider_ip}:{provider_port}")
        print(f"{banner} {filename} parça [{start_b}-{end_b}] indirildi {provider_ip}:{provider_port}")
    except Exception as e:
        print(f"{banner} HATA: {filename} parça [{start_b}-{end_b}] {provider_ip}:{provider_port} -> {e}")

# ---------- Peer'in indirme sunucusu ----------
def serve_downloads(repo_dir: Path, peer_port: int, banner: str):
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("", peer_port))
    srv.listen()
    print(f"{banner} Peer download server aktif...")

    def handler(conn: socket.socket, addr):
        try:
            msg = recv_until_end(conn)
            toks = msg.split()
            if toks[:2] == ["START", "DOWNLOAD"]:
                filename = toks[2]
                start_b = int(toks[3])
                end_b = int(toks[4])
                path = repo_dir / filename
                data = b""
                if path.exists():
                    with open(path, "rb") as f:
                        f.seek(start_b)
                        to_read = end_b - start_b + 1
                        data = f.read(to_read)
                # ikili ham veri yolla
                conn.sendall(data)
        except Exception as e:
            # Sunucu tarafı sessiz hata toleransı
            pass
        finally:
            conn.close()

    while True:
        c, a = srv.accept()
        threading.Thread(target=handler, args=(c, a), daemon=True).start()

# ---------- Ana akış ----------
def main():
    if len(sys.argv) != 5:
        print("Kullanım: python3 peer.py <ServerIP:Port> <RepoDir> <ScheduleFile> <PeerPort>")
        sys.exit(1)

    server_addr = sys.argv[1]
    repo_dir = Path(sys.argv[2]).resolve()
    schedule_path = Path(sys.argv[3]).resolve()
    peer_port = int(sys.argv[4])

    server_ip, server_port = server_addr.split(":")
    server_port = int(server_port)

    banner = f"[{peer_port}]"

    # İndirme sunucusunu başlat
    t_srv = threading.Thread(target=serve_downloads, args=(repo_dir, peer_port, banner), daemon=True)
    t_srv.start()

    time.sleep(0.2)  # çok kısa bekleme, port dinlemeye başlasın

    # Sunucuya SERVING bildir
    try:
        reply = send_cmd(server_ip, server_port, f"START SERVING {peer_port}")
        print(f"{banner} Server’a kaydedildi.")
    except Exception as e:
        print(f"{banner} Sunucuya bağlanılamadı: {e}")
        sys.exit(1)

    # Başlangıç PROVIDING (repo'daki mevcut dosyalar)
    current_files = list_repo_files(repo_dir)
    if current_files:
        joined = " ".join(current_files)
        cmd = f"START PROVIDING {peer_port} {len(current_files)} {joined}"
        try:
            _ = send_cmd(server_ip, server_port, cmd)
        except Exception as e:
            print(f"{banner} Başlangıç PROVIDING hatası: {e}")

    # Schedule oku
    wait_ms, jobs = read_schedule(schedule_path)
    if wait_ms > 0:
        time.sleep(wait_ms / 1000.0)

    # Sırayla dosya ara/indir
    for name, size in jobs:
        print(f"{banner} {name} dosyası aranıyor...")
        # Sağlayıcıları sor
        try:
            resp = send_cmd(server_ip, server_port, f"START SEARCH {name}")
        except Exception as e:
            print(f"{banner} Sunucu SEARCH hatası: {e}")
            continue

        # Beklenen cevap: START PROVIDERS ip:port ip:port ... END
        providers = []
        toks = resp.split()
        if toks[:2] == ["START", "PROVIDERS"]:
            # geri kalanları ip:port biçiminde
            for t in toks[2:-1]:
                if ":" in t:
                    ip, p = t.split(":")
                    try:
                        providers.append((ip, int(p)))
                    except:
                        pass

        # Kendimizi ele
        providers = [(ip, p) for (ip, p) in providers if p != peer_port]

        if not providers:
            print(f"{banner} {name} bulunamadı veya sağlayıcılar hazır değil!")
            continue

        # Hedef dosyayı repo'ya oluştur (pre-allocate)
        dest = repo_dir / name
        # Var ise üzerine yazacağız (yeniden indirilebilirlik)
        with open(dest, "wb") as f:
            if size > 0:
                f.truncate(size)

        # Aralıkları böl ve paralel indir
        ranges = partition_ranges(size, len(providers))
        threads = []
        for (prov, rng) in zip(providers, ranges):
            ip, p = prov
            start_b, end_b = rng
            th = threading.Thread(
                target=download_part,
                args=(p, name, dest, ip, p, start_b, end_b, repo_dir, banner),
                daemon=True
            )
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        # Boyut doğrulaması
        ok = dest.exists() and dest.stat().st_size == size
        if not ok:
            print(f"{banner} UYARI: {name} indirimi eksik olabilir (beklenen {size}, gerçek {dest.stat().st_size if dest.exists() else 0})")
        else:
            print(f"{banner} {name} indirildi.")

        # Bu dosyayı PROVIDING ile duyur
        try:
            _ = send_cmd(server_ip, server_port, f"START PROVIDING {peer_port} 1 {name}")
        except Exception as e:
            print(f"{banner} PROVIDING (tekil) hatası: {e}")

    # Tümü tamamlandı -> done
    with open("done", "w", encoding="utf-8") as f:
        f.write("ok\n")
    print(f"{banner} Tüm indirmeler tamamlandı. 'done' oluşturuldu.")

if __name__ == "__main__":
    main()
