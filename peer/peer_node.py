import os, time
from pathlib import Path
from common.protocol import send_cmd
from common.utils import list_repo_files
from peer.file_server import FileServer
from peer.file_downloader import parallel_download
from peer.schedule_parser import read_schedule


class PeerNode:
    def __init__(self, server_ip: str, server_port: int, repo_dir: str, schedule_path: str, peer_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.repo_dir = Path(repo_dir).resolve()
        self.schedule_path = Path(schedule_path).resolve()
        self.peer_port = peer_port
        self.banner = f"[{peer_port}]"

    def run(self):
        # serving thread (daemon=False)
        FileServer(self.repo_dir, self.peer_port, self.banner).start()
        time.sleep(0.2)

        # SERVING bildir
        try:
            send_cmd(self.server_ip, self.server_port, f"START SERVING {self.peer_port}")
            print(f"{self.banner} Server’a kaydedildi.")
        except Exception as e:
            print(f"{self.banner} Sunucuya bağlanılamadı: {e}")
            return

        # başlangıç PROVIDING (eldeki dosyalar)
        current = list_repo_files(self.repo_dir)
        if current:
            joined = " ".join(current)
            try:
                send_cmd(self.server_ip, self.server_port, f"START PROVIDING {self.peer_port} {len(current)} {joined}")
            except Exception as e:
                print(f"{self.banner} Başlangıç PROVIDING hatası: {e}")

        # schedule
        wait_ms, jobs = read_schedule(self.schedule_path)
        if wait_ms > 0: time.sleep(wait_ms / 1000.0)

        all_ok = True
        for name, size in jobs:
            print(f"{self.banner} {name} dosyası aranıyor...")
            ok = parallel_download(self.banner, self.server_ip, self.server_port, self.peer_port, self.repo_dir, name, size)
            all_ok = all_ok and ok

        # done (hepsi başarılıysa)
        if all_ok:
            with open("done", "w", encoding="utf-8") as f: f.write("ok\n")
            print(f"{self.banner} Tüm indirmeler tamamlandı. 'done' oluşturuldu.")
        else:
            print(f"{self.banner} Bazı dosyalar başarısız; 'done' yazılmadı.")

        try: time.sleep(30)
        except KeyboardInterrupt: pass
