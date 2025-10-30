import socket, threading
from pathlib import Path
from common.protocol import Protocol

class FileProviderServer:
    def __init__(self, repo_dir: Path, peer_port: int):
        self.repo_dir = Path(repo_dir)
        self.peer_port = peer_port

    def _handler(self, conn, addr):
        try:
            msg = Protocol.receive_msg(conn)
            tokens = msg.split()
            if tokens[:2] == ["START", "DOWNLOAD"]:
                filename = tokens[2]
                start_b = int(tokens[3])
                end_b = int(tokens[4])
                to_read = end_b - start_b + 1
                path = self.repo_dir / filename
                if path.exists():
                    with open(path, "rb") as f:
                        f.seek(start_b)
                        while to_read > 0:
                            data = f.read(min(65536, to_read))
                            conn.sendall(data)
                            to_read -= len(data)
        finally:
            conn.close()


    def start(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", self.peer_port))
        s.listen()
        print(f"PEER{self.peer_port} is providing files")
        def loop():
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self._handler, args=(conn, addr), daemon=True).start()
        t = threading.Thread(target=loop)
        t.start()
        return t
