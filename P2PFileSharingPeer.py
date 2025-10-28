from peer.peer_node import PeerNode
import sys

def main():
    if len(sys.argv) != 5:
        print("Usage: python3 P2PFileSharingPeer.py <ServerIP:Port> <RepoDir> <ScheduleFile> <PeerPort>")
        sys.exit(1)
    server_addr, repo_dir, schedule_file, peer_port = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    ip, p = server_addr.split(":")
    node = PeerNode(server_ip=ip, server_port=int(p), repo_dir=repo_dir, schedule_path=schedule_file, peer_port=peer_port)
    node.run()

if __name__ == "__main__":
    main()
