# P2P File Sharing

A Python-based peer-to-peer file sharing system that uses a central registry server for peer discovery and parallel byte-range downloads between peers.

## Overview

This project demonstrates a simple P2P file sharing architecture. A central server keeps track of active peers and the files they provide, while each peer can both serve local files and download missing files from other peers. Downloads are split into byte ranges so multiple providers can transfer different parts of the same file concurrently.

## Features

- Central server for peer registration, provider tracking, and file search.
- Peer nodes that serve local repository files over TCP sockets.
- Parallel downloads from multiple peers using byte-range partitioning.
- Schedule-driven download jobs with configurable startup wait time.
- Test data generation for a three-peer demo environment.
- Lightweight implementation using only the Python standard library.

## Project Structure

```text
.
├── P2PFileSharingServer.py      # Central registry server entry point
├── P2PFileSharingPeer.py        # Peer node entry point
├── common/
│   └── protocol.py              # Shared socket protocol helpers
├── server/
│   ├── file_search_server.py    # Central server socket loop
│   ├── peer_registry.py         # Active peer and file provider registry
│   └── request_handler.py       # Server-side command handling
├── peer/
│   ├── file_provider.py         # Peer file serving socket
│   ├── file_downloader.py       # Parallel download logic
│   ├── peer_server.py           # Peer lifecycle orchestration
│   └── schedule_parser.py       # Schedule file parser
├── example/                     # Example peer schedules and setup notes
├── create_test_data.py          # Generates demo peer repositories
├── start_p2p_tmux.sh            # Optional tmux launcher
└── run_all.bat                  # Optional Windows launcher
```

## Requirements

- Python 3.9 or newer recommended.
- No third-party Python packages are required.

## Quick Start

### 1. Generate demo files

```bash
python3 create_test_data.py
```

This creates three local repositories:

- `peer1-repo`
- `peer2-repo`
- `peer3-repo`

Each repository contains sample `.dat` files used by the demo schedules.

### 2. Start the central server

Open a terminal and run:

```bash
python3 P2PFileSharingServer.py 5001
```

### 3. Start peers

Open three additional terminals and run one peer in each terminal:

```bash
python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer1-repo example/peer1-schedule.txt 6001
```

```bash
python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer2-repo example/peer2-schedule.txt 6002
```

```bash
python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer3-repo example/peer3-schedule.txt 6003
```

## Command Reference

### Server

```bash
python3 P2PFileSharingServer.py <Port>
```

Example:

```bash
python3 P2PFileSharingServer.py 5001
```

### Peer

```bash
python3 P2PFileSharingPeer.py <ServerIP:Port> <RepoDir> <ScheduleFile> <PeerPort>
```

Example:

```bash
python3 P2PFileSharingPeer.py 127.0.0.1:5001 peer1-repo example/peer1-schedule.txt 6001
```

## Schedule File Format

Schedule files define when a peer starts and which files it should download.

```text
wait 500
e.dat:00104857600
f.dat:00209715200
```

- `wait <milliseconds>` delays the peer before it starts processing download jobs.
- `<filename>:<size>` requests a file and provides the expected file size in bytes.

## How It Works

1. The central server starts and waits for peer connections.
2. Each peer starts its own file provider server on the configured peer port.
3. Each peer registers itself with the central server using `START SERVING`.
4. Each peer sends its available file list using `START PROVIDING`.
5. When a schedule requests a file, the peer searches the central server using `START SEARCH`.
6. The central server returns available providers.
7. The downloading peer splits the target file into byte ranges and downloads parts in parallel from providers.
8. After a successful download, the peer registers the newly downloaded file as available for other peers.

## Output Files

- `download.log`: records which providers were used for downloaded file parts.
- `done`: created when a peer completes all scheduled downloads successfully.

## Notes

- Run all commands from the project root directory.
- Make sure each peer uses a unique port.
- If a port is already in use, stop the previous process or choose a different port.
- The included demo files are large sparse files, so their apparent size may be larger than the actual disk space used depending on the operating system.

## License

No license has been specified for this repository.
