#!/usr/bin/env python3

"""
Utility to backup restore database.

Mandatory for a try and trial approach.
Needed:
sudo apt install -y mongodb-database-tools
"""

import argparse
import datetime
import os
import subprocess
import sys


def run(cmd: list[str]) -> None:
    """Run."""
    print(">>>", " ".join(cmd))
    subprocess.check_call(cmd)


def backup(args: argparse.Namespace) -> None:
    """Backup database."""

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = f"{args.output}/{args.db}-{ts}"
    os.makedirs(backup_dir, exist_ok=True)

    cmd = [
        "mongodump",
        "--host", args.host,
        "--port", str(args.port),
        "--db", args.db,
        "--out", backup_dir,
        "--gzip",
        "--authenticationMechanism", "SCRAM-SHA-256"
    ]

    if args.user:
        cmd += ["--username", args.user, "--password", args.password]

    run(cmd)
    print(f"\n✅ Backup finished : {backup_dir}")


def restore(args: argparse.Namespace) -> None:
    """Restore database."""

    if not os.path.exists(args.input):
        print("❌ Backup directory not found")
        sys.exit(1)

    if not args.force:
        confirm = input(f"⚠️  This will OVERRIDE base '{args.db}'. Continue ? (y/N) ")
        if confirm.lower() != 'y':
            print("⛔ Abort")
            sys.exit(0)

    cmd = [
        "mongorestore",
        "--host", args.host,
        "--port", str(args.port),
        "--db", args.db,
        "--drop",
        "--gzip",
        "--authenticationMechanism", "SCRAM-SHA-256",
        args.input + "/" + args.db
    ]

    if args.user:
        cmd += ["--username", args.user, "--password", args.password]

    run(cmd)
    print(f"\n✅ Restore done from : {args.input}")


def main() -> None:
    """Main."""

    parser = argparse.ArgumentParser(description="Backup / Restore MongoDB")
    sub = parser.add_subparsers(dest="action", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", default="37.59.100.228")
    common.add_argument("--port", default=27017, type=int)
    common.add_argument("--db", default="nodebb")
    common.add_argument("--user", default="nodebb")
    common.add_argument("--password", default="nodebb123")

    b = sub.add_parser("backup", parents=[common])
    b.add_argument("--output", default="./backups")

    r = sub.add_parser("restore", parents=[common])
    r.add_argument("--input", required=True)
    r.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.action == "backup":
        backup(args)
    elif args.action == "restore":
        restore(args)


if __name__ == "__main__":
    main()
