import socket

END = b" END"

class Protocol:
    @staticmethod
    def receive_msg(sock: socket.socket) -> str:
        buf = b""
        while END not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        return buf.decode().strip()

    @staticmethod
    def _send_cmd(sock: socket.socket, cmd: str, *args) -> None:
        """Send a command over an existing socket. Does not receive a reply."""
        parts = [cmd] + [str(a) for a in args]
        text = " ".join(parts) + " END"
        sock.sendall(text.encode())

    @staticmethod
    def start_serving(sock: socket.socket, port: int) -> None:
        Protocol._send_cmd(sock, "START SERVING", port)

    @staticmethod
    def start_providing(sock: socket.socket, port: int, file_list: list) -> None:
        # Peer -> Server: START PROVIDING <port> <n> <name1> <name2> ... END
        Protocol._send_cmd(sock, "START PROVIDING", port, len(file_list), *file_list)

    @staticmethod
    def stop_serving(sock: socket.socket, port: int) -> None:
        Protocol._send_cmd(sock, "STOP SERVING", port)

    @staticmethod
    def start_search(sock: socket.socket, query: str) -> None:
        Protocol._send_cmd(sock, "START SEARCH", query)

    @staticmethod
    def start_providers(sock: socket.socket, file_list: list) -> None:
        # Server -> Peer: START PROVIDERS <ip:port> <ip:port> ... END
        Protocol._send_cmd(sock, "START PROVIDERS", *file_list)

    @staticmethod
    def start_download(sock: socket.socket, filename: str, start_b: int, end_b: int) -> None:
        # Peer -> Provider: START DOWNLOAD <filename> <start> <end> END
        Protocol._send_cmd(sock, "START DOWNLOAD", filename, start_b, end_b)

