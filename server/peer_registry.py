from collections import defaultdict

class PeerRegistry:
    """
    - providers: {filename -> set((ip, port))}
    - peer_files: {(ip, port) -> set(filename)}  # fast reverse lookup for deletions
    """
    def __init__(self):
        self.active_peers = set()  # set((ip, port))
        self.providers = defaultdict(set)  # {filename: set((ip, port))}
        self.peer_files = defaultdict(set)  # {(ip, port): set(filename)}

    def register_peer(self, addr_ip: str, port: int):
        peer = (addr_ip, port)
        self.active_peers.add(peer)
        print(f"Peer {peer} registered as active.")

    def delete_peer(self, addr_ip: str, port: int):
        peer = (addr_ip, port)
        if peer in self.active_peers:
            self.active_peers.discard(peer)
            print(f"Peer {peer} removed from active peers.")
        else:
            print(f"Peer {peer} not found in active peers.")

        filenames = self.peer_files.pop(peer, set())
        for name in filenames:
            self.providers.get(name).discard(peer)
            print(f"Peer {peer} removed as provider for file '{name}'.")
            if not self.providers.get(name):
                del self.providers[name]

    def register_providing(self, addr_ip: str, port: int, names):
        peer = (addr_ip, port)
        for name in names:
            self.providers[name].add(peer)
            self.peer_files[peer].add(name)
            print(f"Peer {peer} registered as provider for file '{name}'.")

    def search(self, filename: str):
        peers = list(self.providers.get(filename, set()))
        if peers:
            print(f"File '{filename}' is provided by peers: {peers}")
        else:
            print(f"No providers found for file '{filename}'.")
        return peers
