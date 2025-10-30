import os
from pathlib import Path

# Her peer’ın dizinini tanımla
repos = {
    "peer1-repo": ["a.dat", "b.dat", "c.dat", "d.dat"],
    "peer2-repo": ["c.dat", "d.dat", "e.dat", "f.dat"],
    "peer3-repo": ["e.dat", "f.dat", "g.dat", "h.dat"],
}

# Boyutları byte cinsinden belirle (örnek)
# 100MB = 100 * 1024 * 1024 = 104857600
# 200MB = 200 * 1024 * 1024 = 209715200
sizes = {
    "small": 104857600,   # 100 MB
    "large": 209715200,   # 200 MB
}

# a,c,e,g küçük dosya, b,d,f,h büyük dosya olacak
size_map = {
    "a.dat": sizes["small"],
    "b.dat": sizes["large"],
    "c.dat": sizes["small"],
    "d.dat": sizes["large"],
    "e.dat": sizes["small"],
    "f.dat": sizes["large"],
    "g.dat": sizes["small"],
    "h.dat": sizes["large"],
}

for repo, files in repos.items():
    Path(repo).mkdir(exist_ok=True)
    for fname in files:
        path = Path(repo) / fname
        if not path.exists():
            with open(path, "wb") as f:
                f.truncate(size_map[fname])
            print(f"✅ {path} created with size {size_map[fname] // 1024 // 1024} MB")
        else:
            print(f"⚠️ {path} already exists")
