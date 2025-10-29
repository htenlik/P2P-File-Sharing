import socket
from enum import Enum

END = b" END"

class Command(Enum):
    START_SERVING = "START SERVING"
    START_PROVIDING = "START PROVIDING"
    STOP_SERVING = "STOP SERVING"
    START_SEARCH = "START SEARCH"
    START_PROVIDERS = "START PROVIDERS"
    START_DOWNLOAD = "START DOWNLOAD"


def receive_msg(sock: socket.socket) -> str:
    buf = b""
    while END not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf.decode().strip()

def send_cmd(sock: socket.socket, cmd: Command, *args) -> None:
    """Send a command over an existing socket. Does not receive a reply."""
    parts = [cmd.value] + [str(a) for a in args]
    text = " ".join(parts) + " END"
    sock.sendall(text.encode())

def send_and_receive_cmd(ip: str, port: int, cmd: Command, *args) -> str:
    """Open a socket, send the command, receive the reply, and return it."""
    s = socket.socket()
    try:
        s.connect((ip, port))
        send_cmd(s, cmd, *args)
        reply = receive_msg(s)
        return reply
    finally:
        s.close()
