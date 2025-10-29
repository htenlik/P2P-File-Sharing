import time
from pathlib import Path
from common.protocol import send_and_receive_cmd, Command
from peer.file_provider import FileProviderServer
from peer.file_downloader import parallel_download
from peer.schedule_parser import read_schedule


class PeerNode:
    def __init__(self, server_ip: str, server_port: int, repo_dir: str, schedule_path: str, peer_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.repo_dir = Path(repo_dir).resolve()
        self.schedule_path = Path(schedule_path).resolve()
        self.peer_port = peer_port

    def register_peer_to_server(self) -> bool:
        """Register this peer to the central server (START SERVING)."""
        try:
            send_and_receive_cmd(self.server_ip, self.server_port, Command.START_SERVING, self.peer_port)
            print(f"PEER{self.peer_port} is registered to SERVER at {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"PEER{self.peer_port} cannot registered to SERVER {e}")
            time.sleep(10)
            return False

    def send_file_list_to_server(self) -> bool:
        """Send current file list to server (START PROVIDING)."""
        file_list = [p.name for p in Path(self.repo_dir).iterdir() if p.is_file()]
        if file_list:
            try:
                send_and_receive_cmd(self.server_ip, self.server_port, Command.START_PROVIDING, self.peer_port, len(file_list), *file_list)
            except Exception as e:
                print(f"PEER{self.peer_port} cannot Provide File List while initializing peer: {e}")
                time.sleep(10)
                return False
        return True

    def execute_schedule(self) -> None:
        """Process the schedule: search/download files, then gracefully unregister."""
        wait_ms, jobs = read_schedule(self.schedule_path)
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

        all_files_downloaded = True
        for name, size in jobs:
            print(f"PEER{self.peer_port} {name} dosyası aranıyor...")
            is_download_successful = parallel_download(self.server_ip, self.server_port, self.peer_port, self.repo_dir, name, size)
            if not is_download_successful:
                all_files_downloaded = False

        if all_files_downloaded:
            with open("done", "w", encoding="utf-8") as f:
                f.write("ok\n")
            print(f"PEER{self.peer_port} all files downloaded successfully; 'done' file created.")
        else:
            print(f"PEER{self.peer_port} some files failed to download!")

        try:
            time.sleep(30)
        finally:
            # it must work with ctrl + C interrupt too
            try:
                send_and_receive_cmd(self.server_ip, self.server_port, Command.STOP_SERVING, self.peer_port)
                print(f"PEER{self.peer_port} is unregistered from SERVER")
            except Exception as e:
                print(f"PEER{self.peer_port} cannot unregister from SERVER {e}")

    def run(self):
        FileProviderServer(self.repo_dir, self.peer_port).start()
        if not self.register_peer_to_server():
            return
        if not self.send_file_list_to_server():
            return
        self.execute_schedule()
