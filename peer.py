import socket, threading, os, time

END = b" END"

def send_cmd(ip, port, text):
    with socket.create_connection((ip, port)) as s:
        s.sendall(text.encode())
        return s.recv(65536).decode(errors="ignore")

def download_part(peer_ip, peer_port, fname, start, end, outpath):
    with socket.create_connection((peer_ip, peer_port)) as s:
        cmd = f"START DOWNLOAD {fname} {start} {end} END".encode()
        s.sendall(cmd)
        with open(outpath, "wb") as f:
            while True:
                chunk = s.recv(1024)
                if not chunk: break
                f.write(chunk)

def split_ranges(size, k):
    base = size // k
    cur = 0
    ranges = []
    for i in range(k):
        ranges.append((cur, cur + base - 1))
        cur += base
    return ranges

def combine_parts(part_files, final_path):
    with open(final_path, "wb") as out:
        for p in part_files:
            with open(p, "rb") as f:
                out.write(f.read())
            os.remove(p)

def run_peer(server_ip, server_port, my_port, repo_dir, schedule_file):
    send_cmd(server_ip, server_port, f"START SERVING {my_port} END")

    files = os.listdir(repo_dir)
    if files:
        send_cmd(server_ip, server_port,
                 f"START PROVIDING {my_port} {len(files)} " + " ".join(files) + " END")

    print("Peer hazır! Schedule okunuyor...")

    with open(schedule_file) as f:
        lines = [l.strip() for l in f if l.strip()]
    wait_ms = int(lines[0].split()[1])
    time.sleep(wait_ms / 1000)
    targets = [l.split(":") for l in lines[1:]]

    for name, size_str in targets:
        size = int(size_str)
        reply = send_cmd(server_ip, server_port, f"START SEARCH {name} END")
        print("Server cevabı:", reply)

    open("done", "w").close()

if __name__ == "__main__":
    import sys
    ip, port = sys.argv[1].split(":")
    run_peer(ip, int(port), 6000, "./peer1-repo", "peer1-schedule.txt")
