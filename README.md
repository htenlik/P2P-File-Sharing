# P2P-File-Sharing
 
# Nasıl çalıştırılır?

## Dosyaları oluştur

`python3 create_test_data.py
`

## Sunucuyu başlat

### Yeni terminal aç:

`python3 server.py 5001
`

## 3 ayrı terminal aç:

### Peer1:

`python3 peer.py 127.0.0.1:5001 peer1-repo example/peer1-schedule.txt 6001
`

### Peer2:

`python3 peer.py 127.0.0.1:5001 peer2-repo example/peer2-schedule.txt 6002
`

### Peer3:

`python3 peer.py 127.0.0.1:5001 peer3-repo example/peer3-schedule.txt 6003
`

# Ne göreceksin?

Her peer kendi portunda “Peer download server aktif...” diye yazar.

Server terminalinde bağlantılar akar.

Peer’ler sırayla dosya arar, paralel indirir, peer.log ve done dosyalarını oluşturur.

