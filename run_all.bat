@echo off
echo [1/5] Test verisi oluşturuluyor...
start cmd /k "python create_test_data.py"
timeout /t 4 >nul

echo [2/5] Sunucu baslatiliyor...
start cmd /k "python P2PFileSharingServer.py 5001"
timeout /t 4 >nul

echo [3/5] Peer1 baslatiliyor...
start cmd /k "python P2PFileSharingPeer.py 127.0.0.1:5001 peer2-repo example/peer2-schedule.txt 6002"

echo [4/5] Peer2 baslatiliyor...
start cmd /k "python P2PFileSharingPeer.py 127.0.0.1:5001 peer3-repo example/peer3-schedule.txt 6003"

echo [5/5] Peer3 baslatiliyor...
start cmd /k "python P2PFileSharingPeer.py 127.0.0.1:5001 peer1-repo example/peer1-schedule.txt 6001"

echo Tum processler baslatildi!
pause