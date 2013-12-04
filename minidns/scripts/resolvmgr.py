
""" This handles the management of /etc/resolv.conf. It's pretty fugly to be honest.

On starting it:

  1. copies /etc/resolv.conf to /etc/resolv.conf.minidns
  2. writes a new /etc/resolv.conf that uses 127.0.0.1 as the nameserver
  
It then regularly checks the modification date on /etc/resolv.conf. If it is newer than the last change it made itself then it rewrites it again.

On exit it moves /etc/resolv.conf.minidns to /etc/resolv.conf

"""

import os
import sys
import atexit
import threading
import signal
import stat
import time

timer = None
timestamp = None

def rewrite_resolvconf():
    # don't do atomic moves, because /etc/resolv.conf is quite possibly a symlink
    resolvconf = open("/etc/resolv.conf", "w")
    print >> resolvconf, "nameserver 127.0.0.1"
    for l in open("/etc/resolv.conf.minidns"):
        if not l.startswith("nameserver") and not l.startswith("#"):
            resolvconf.write(l)
    resolvconf.close()
    global timestamp
    timestamp = time.time()

def exit(*args, **kwargs):
    if timer is not None:
        timer.cancel()
    if os.path.exists("/etc/resolv.conf.minidns"):
        open("/etc/resolv.conf", "w").write(open("/etc/resolv.conf.minidns").read())
        os.unlink("/etc/resolv.conf.minidns")
    
def check():
    mtime = os.stat("/etc/resolv.conf")[stat.ST_MTIME]
    if mtime > timestamp:
        rewrite_resolvconf()
    global timer
    timer = threading.Timer(1, check)
    timer.start()
    
def run():
    pid = os.fork()
    if pid < 0:
        sys.exit(1)
    elif pid != 0:
        sys.exit(0)
    pid = os.setsid()
    if pid == -1:
        sys.exit(1)
    print os.getpid()
    sys.stderr.close()
    sys.stdout.close()
    sys.stdin.close()
    os.chdir("/")
    signal.signal(signal.SIGTERM, exit)
    atexit.register(exit)
    open("/etc/resolv.conf.minidns.tmp", "w").write(open("/etc/resolv.conf").read())
    os.rename("/etc/resolv.conf.minidns.tmp", "/etc/resolv.conf.minidns")
    rewrite_resolvconf()
    global timer
    timer = threading.Timer(1, check)
    timer.start()
    
    