#!/bin/bash

# TMUX oturum adı
SESSION_NAME="p2p"

# Eğer zaten çalışıyorsa, önce durdur
tmux has-session -t $SESSION_NAME 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Önceki tmux oturumu bulunuyor, kapatılıyor..."
    tmux kill-session -t $SESSION_NAME
fi

echo "Yeni tmux oturumu oluşturuluyor: $SESSION_NAME"

# 1. Pencere: create_test_data.py
tmux new-session -d -s $SESSION_NAME -n create "python3 create_test_data.py; sleep 4; bash"

# 2. Pencere: Sunucu
tmux new-window -t $SESSION_NAME:1 -n server "python3 P2PFileSharingServer.py 5001; bash"

# 3. Pencere: Peer1
tmux new-window -t $SESSION_NAME:2 -n peer1 "python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer2-repo example/peer2-schedule.txt 6002; bash"

# 4. Pencere: Peer2
tmux new-window -t $SESSION_NAME:3 -n peer2 "python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer3-repo example/peer3-schedule.txt 6003; bash"

# 5. Pencere: Peer3
tmux new-window -t $SESSION_NAME:4 -n peer3 "python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer1-repo example/peer1-schedule.txt 6001; bash"

echo "Tüm processler tmux içinde başlatıldı!"
echo "Bağlanmak için: tmux attach -t $SESSION_NAME"
