#!/usr/bin/env python3

import sqlite3
import subprocess
import gzip
import shutil
import logging

from datetime import datetime
from pathlib import Path



# ================= CONFIG =================
 

SRC_DB = Path("/var/data/ma_base.db")
WORKDIR = Path("/var/backups/sqlite_tmp")
REMOTE = backup@192.168.1.50:/data/sqlite/
KEEP_DAYS = 14
 

# ==========================================


WORKDIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_db = WORKDIR / f"ma_base_{timestamp}.db"
backup_gz = backup_db.with_suffix(".db.gz")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Début sauvegarde SQLite")

# 1️⃣ Backup SQLite atomique

with sqlite3.connect(SRC_DB) as src:
    with sqlite3.connect(backup_db) as dst:
        src.backup(dst)

logging.info("Backup local OK")


# 2️⃣ Vérification intégrité

result = subprocess.run(
    ["sqlite3", backup_db, "PRAGMA integrity_check;"],
    capture_output=True,
    text=True
)

if result.stdout.strip() != "ok":
    raise RuntimeError("❌ Base corrompue")

logging.info("Intégrité SQLite OK")
 

# 3️⃣ Compression

with open(backup_db, "rb") as f_in, gzip.open(backup_gz, "wb") as f_out:
    shutil.copyfileobj(f_in, f_out)

backup_db.unlink()
logging.info("Compression OK")


# 4️⃣ Transfert SCP

subprocess.run(
    ["scp", backup_gz, REMOTE],
    check=True
)

logging.info("Transfert distant OK")

# 5️⃣ Rotation locale

now = datetime.now().timestamp()
for f in WORKDIR.glob("*.gz"):
    if f.stat().st_mtime < now - KEEP_DAYS * 86400:
        f.unlink()

logging.info("Rotation terminée")
logging.info("Sauvegarde terminée avec succès")
