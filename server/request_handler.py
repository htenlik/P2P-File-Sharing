from common.protocol import receive_msg, send_cmd, Command

class RequestHandler:
    def __init__(self, conn, addr, registry):
        self.conn = conn
        self.addr = addr
        self.registry = registry

    def run(self):
        try:
            msg = receive_msg(self.conn).strip()
            tokens = msg.split()
            if tokens[:2] == ["START", "SERVING"]:
                port = int(tokens[2])
                self.registry.register_peer(self.addr[0], port)
            elif tokens[:2] == ["STOP", "SERVING"]:
                port = int(tokens[2])
                self.registry.delete_peer(self.addr[0], port)
            elif tokens[:2] == ["START", "PROVIDING"]:
                port = int(tokens[2]); n = int(tokens[3])
                names = tokens[4:-1][:n]
                self.registry.register_providing(self.addr[0], port, names)
            elif tokens[:2] == ["START", "SEARCH"]:
                name = tokens[2]
                peers = self.registry.search(name)
                send_cmd(self.conn, Command.START_PROVIDERS, *[f"{ip}:{p}" for (ip, p) in peers])
        finally:
            self.conn.close()
