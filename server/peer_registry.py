from collections import defaultdict

class PeerRegistry:
    """
    - ports: {port -> ip}
    - providers: {filename -> set((ip, port))}
    """
    def __init__(self):
        self.ports = {}  # {port: ip}
        self.providers = defaultdict(set)  # {filename: set((ip, port))}

    def register_serving(self, ip: str, port: int):
        self.ports[port] = ip

    def register_providing(self, addr_ip: str, port: int, names):
        ip = self.ports.get(port, addr_ip)
        for name in names:
            self.providers[name].add((ip, port))

    def search(self, filename: str):
        return list(self.providers.get(filename, set()))
