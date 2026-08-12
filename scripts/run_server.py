#!/usr/bin/env python3
"""Daemonize uvicorn (double-fork + setsid) so it survives shell teardown.

Usage: python3 scripts/run_server.py [--port 8091] [--mock]
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)

port = "8091"
mock = False
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--port" and i + 1 < len(args):
        port = args[i + 1]
        i += 2
    elif args[i] == "--mock":
        mock = True
        i += 1
    else:
        i += 1

env = dict(os.environ)
if mock:
    env["MOCK_DB"] = "1"

cmd = [sys.executable, "-m", "uvicorn", "main:app",
       "--host", "127.0.0.1", "--port", port]


def daemonize(logpath):
    if os.fork() > 0:
        return False
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    devnull = os.open(os.devnull, os.O_RDWR)
    log = os.open(logpath, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    os.dup2(devnull, 0)
    os.dup2(log, 1)
    os.dup2(log, 2)
    os.chdir(HERE)
    return True


if not daemonize(os.path.join(HERE, "uvicorn.log")):
    sys.exit(0)

proc = subprocess.Popen(cmd, env=env)
with open("/tmp/opencode/uvicorn.pid", "w") as f:
    f.write(str(proc.pid))

# wait for health
import urllib.request

for _ in range(30):
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:%s/health" % port, timeout=1
        ) as r:
            sys.exit(0 if r.status == 200 else 1)
    except Exception:
        time.sleep(0.5)
sys.exit(1)
