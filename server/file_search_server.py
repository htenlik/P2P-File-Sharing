import socket
import threading
from server.peer_registry import PeerRegistry
from server.request_handler import RequestHandler

class CentralServer:
    def __init__(self, port: int):
        self.port = port
        self.registry = PeerRegistry()

    def run(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", self.port))
        s.listen()
        print(f"Server started on port {self.port}")
        while True:
            conn, addr = s.accept()
            handler = RequestHandler(conn, addr, self.registry)
            t = threading.Thread(target=handler.run, daemon=True)
            t.start()
