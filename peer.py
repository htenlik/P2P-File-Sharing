import socket, threading, os, time

END = b" END"
CHUNK = 1024 * 1024  # 1MB okuma/yazma buffer

# --------------------- yardımcı fonksiyonlar ---------------------

def recv_until_end(conn):
    """END kelimesine kadar tüm veriyi oku ve döndür."""
    buf = b""
    while END not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf.decode()

def send_cmd(ip, port, text):
    """Server veya peer'e komut gönder, cevap döndür."""
    with socket.create_connection((ip, port)) as s:
        s.sendall(text.encode())
        reply = b""
        while True:
            part = s.recv(4096)
            if not part:
                break
            reply += part
            if b"END" in reply:
                break
        return reply.decode(errors="ignore")

# --------------------- server iletişimi ---------------------

def register_to_server(server_ip, server_port, my_port, repo_dir):
    """Server'a kendi portunu ve mevcut dosyaları bildir."""
    # 1. SERVING
    send_cmd(server_ip, server_port, f"START SERVING {my_port} END")

    # 2. PROVIDING (repo’daki tüm dosyalar)
    files = [f for f in os.listdir(repo_dir) if os.path.isfile(os.path.join(repo_dir, f))]
    if files:
        send_cmd(server_ip, server_port,
                 f"START PROVIDING {my_port} {len(files)} " + " ".join(files) + " END")

# --------------------- dosya gönderici (sunucu) ---------------------

def serve_files(my_port, repo_dir):
    """Diğer peer'lerin bizden dosya isteyebilmesi için sunucu başlat."""
    def handle_peer(conn, addr):
        try:
            msg = recv_until_end(conn).strip()
            tokens = msg.split()
            if tokens[:2] == ["START", "DOWNLOAD"]:
                fname, start, end = tokens[2], int(tokens[3]), int(tokens[4])
                path = os.path.join(repo_dir, fname)
                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(CHUNK, remaining))
                        if not chunk:
                            break
                        conn.sendall(chunk)
                        remaining -= len(chunk)
        except Exception as e:
            print("Download error:", e)
        finally:
            conn.close()

    s = socket.socket()
    s.bind(("", my_port))
    s.listen()
    print(f"[{my_port}] Peer download server aktif...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()

# --------------------- dosya indirme (client) ---------------------

def split_ranges(size, n):
    """Dosyayı n parçaya böl, (start,end) listesi döndür."""
    base = size // n
    rem = size % n
    cur = 0
    ranges = []
    for i in range(n):
        inc = base + (1 if i < rem else 0)
        ranges.append((cur, cur + inc - 1))
        cur += inc
    return ranges

def download_part(peer_ip, peer_port, fname, start, end, outpath):
    """Belirtilen aralıktaki dosya parçasını indir."""
    try:
        with socket.create_connection((peer_ip, peer_port)) as s:
            cmd = f"START DOWNLOAD {fname} {start} {end} END".encode()
            s.sendall(cmd)
            with open(outpath, "wb") as f:
                remaining = end - start + 1
                while remaining > 0:
                    chunk = s.recv(min(CHUNK, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
    except Exception as e:
        print(f"Download part error from {peer_ip}:{peer_port}", e)

def combine_parts(part_files, final_path):
    """İndirilen parça dosyalarını birleştir."""
    with open(final_path, "wb") as out:
        for p in part_files:
            with open(p, "rb") as f:
                while True:
                    data = f.read(CHUNK)
                    if not data:
                        break
                    out.write(data)
            os.remove(p)

# --------------------- ana peer akışı ---------------------

def run_peer(server_ip, server_port, repo_dir, schedule_file, my_port):
    # 1. kendi dosya sunucusunu arka planda başlat
    threading.Thread(target=serve_files, args=(my_port, repo_dir), daemon=True).start()

    # 2. server’a kendini bildir
    register_to_server(server_ip, server_port, my_port, repo_dir)
    print(f"[{my_port}] Server’a kaydedildi.")

    # 3. schedule oku
    with open(schedule_file) as f:
        lines = [l.strip() for l in f if l.strip()]
    wait_ms = int(lines[0].split()[1])
    time.sleep(wait_ms / 1000)
    targets = [l.split(":") for l in lines[1:]]  # [(dosya, boyut)]

    for name, size_str in targets:
        size = int(size_str)
        print(f"[{my_port}] {name} dosyası aranıyor...")

        # server'dan kimde olduğunu öğren
        reply = send_cmd(server_ip, server_port, f"START SEARCH {name} END")
        parts = reply.split("PROVIDERS", 1)[-1].rsplit("END", 1)[0].strip().split()
        providers = [p.split(":") for p in parts if ":" in p]

        if not providers:
            print(f"[{my_port}] {name} bulunamadı!")
            continue

        # paralel indirme
        ranges = split_ranges(size, len(providers))
        part_files = []
        threads = []
        for i, ((ip, p), (a, b)) in enumerate(zip(providers, ranges)):
            outp = os.path.join(repo_dir, f".{name}.part{i}")
            part_files.append(outp)
            t = threading.Thread(target=download_part, args=(ip, int(p), name, a, b, outp))
            t.start()
            threads.append(t)

        for t in threads: t.join()

        final_path = os.path.join(repo_dir, name)
        combine_parts(part_files, final_path)
        print(f"[{my_port}] {name} indirildi ve birleştirildi ✅")

        # server’a PROVIDING bildir
        send_cmd(server_ip, server_port, f"START PROVIDING {my_port} 1 {name} END")

        # log’a yaz
        with open("peer.log", "a") as logf:
            logf.write(f"{name} {server_ip}:{server_port}\n")

    open("done", "w").close()
    print(f"[{my_port}] Tüm indirmeler tamamlandı. 'done' oluşturuldu.")

# --------------------- çalıştırma noktası ---------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Kullanım: python peer.py <ServerIP:Port> <RepoDir> <ScheduleFile> <MyPort>")
        exit(1)

    ip, port = sys.argv[1].split(":")
    run_peer(ip, int(port), sys.argv[2], sys.argv[3], int(sys.argv[4]))
