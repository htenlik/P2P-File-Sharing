from server.central_server import CentralServer
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 P2PFileSharingServer.py <Port>")
        sys.exit(1)
    port = int(sys.argv[1])
    srv = CentralServer(port)
    srv.serve_forever()

if __name__ == "__main__":
    main()
