import socket

END = b" END"

def recv_until_end(sock: socket.socket) -> str:
    buf = b""
    while END not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf.decode().strip()

def send_cmd(ip: str, port: int, text: str) -> str:
    s = socket.socket()
    s.connect((ip, port))
    s.sendall((text + " END").encode())
    reply = recv_until_end(s)
    s.close()
    return reply
