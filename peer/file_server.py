import socket, threading
from pathlib import Path
from common.protocol import recv_until_end

class FileServer:
    def __init__(self, repo_dir: Path, peer_port: int, banner: str):
        self.repo_dir = Path(repo_dir)
        self.peer_port = peer_port
        self.banner = banner

    def _handler(self, conn, addr):
        try:
            msg = recv_until_end(conn)
            toks = msg.split()
            if toks[:2] == ["START", "DOWNLOAD"]:
                filename = toks[2]
                start_b = int(toks[3]); end_b = int(toks[4])
                to_read = end_b - start_b + 1
                path = self.repo_dir / filename

                sent = 0
                if path.exists():
                    with open(path, "rb") as f:
                        f.seek(start_b)
                        while sent < to_read:
                            need = min(65536, to_read - sent)
                            data = f.read(need)
                            if not data: break
                            conn.sendall(data)
                            sent += len(data)
                if sent < to_read:
                    conn.sendall(b"\x00" * (to_read - sent))
        finally:
            conn.close()

    def start(self):
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", self.peer_port))
        srv.listen()
        print(f"{self.banner} Peer download server aktif...")
        def loop():
            while True:
                c, a = srv.accept()
                threading.Thread(target=self._handler, args=(c, a), daemon=True).start()
        t = threading.Thread(target=loop)  # daemon=False -> process kalıcı
        t.start()
        return t
