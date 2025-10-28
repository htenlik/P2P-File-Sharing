import threading
from common.protocol import recv_until_end
from server.peer_registry import PeerRegistry

class RequestHandler(threading.Thread):
    def __init__(self, conn, addr, registry: PeerRegistry):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.r = registry

    def run(self):
        try:
            msg = recv_until_end(self.conn).strip()
            toks = msg.split()
            if toks[:2] == ["START", "SERVING"]:
                port = int(toks[2])
                self.r.register_serving(self.addr[0], port)

            elif toks[:2] == ["START", "PROVIDING"]:
                port = int(toks[2]); n = int(toks[3])
                names = toks[4:-1][:n]
                self.r.register_providing(self.addr[0], port, names)

            elif toks[:2] == ["START", "SEARCH"]:
                name = toks[2]
                peers = self.r.search(name)
                lst = " ".join([f"{ip}:{p}" for (ip, p) in peers])
                reply = f"START PROVIDERS {lst} END".encode()
                self.conn.sendall(reply)
        finally:
            self.conn.close()
