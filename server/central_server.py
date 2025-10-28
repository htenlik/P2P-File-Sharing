import socket
from server.peer_registry import PeerRegistry
from server.request_handler import RequestHandler

class CentralServer:
    def __init__(self, port: int):
        self.port = port
        self.registry = PeerRegistry()

    def serve_forever(self):
        s = socket.socket()
        s.bind(("", self.port))
        s.listen()
        print(f"Server started on port {self.port}")
        while True:
            conn, addr = s.accept()
            RequestHandler(conn, addr, self.registry).start()
