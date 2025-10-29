from server.file_search_server import CentralServer
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 P2PFileSharingServer.py <Port>")
        sys.exit(1)
    port = int(sys.argv[1])
    server = CentralServer(port)
    server.run()

if __name__ == "__main__":
    main()
