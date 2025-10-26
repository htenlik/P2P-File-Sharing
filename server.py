import socket, threading

providers = {}  # {filename: set((ip, port))}
ports = {}      # {port: ip}

END = b" END"

def recv_until_end(conn):
    buf = b""
    while END not in buf:
        buf += conn.recv(4096)
    return buf.decode()

def handle_client(conn, addr):
    msg = recv_until_end(conn).strip()
    tokens = msg.split()
    if tokens[:2] == ["START", "SERVING"]:
        port = int(tokens[2])
        ports[port] = addr[0]
    elif tokens[:2] == ["START", "PROVIDING"]:
        port = int(tokens[2])
        n = int(tokens[3])
        ip = ports.get(port, addr[0])
        names = tokens[4:-1]
        for name in names[:n]:
            providers.setdefault(name, set()).add((ip, port))
    elif tokens[:2] == ["START", "SEARCH"]:
        name = tokens[2]
        lst = " ".join([f"{ip}:{p}" for (ip,p) in providers.get(name, set())])
        reply = f"START PROVIDERS {lst} END".encode()
        conn.sendall(reply)
    conn.close()

def main(port):
    s = socket.socket()
    s.bind(("", port))
    s.listen()
    print(f"Server started on port {port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]))
