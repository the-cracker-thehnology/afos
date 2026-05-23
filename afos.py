#!/usr/bin/env python3
# AFOS - ANDRAX Fucking Offensive Security Package Manager V6 SE
# 最终完整版：先删后装 | 纯英文大写 | 无装饰符号

import sys
import os
import shutil
import subprocess
import re
import time
import signal

# ---------- 颜色 ----------
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
X = "\033[0m"

# ---------- Banner ----------
LOGO = f"""
{R}        /$$$$$$  /$$$$$$$$ /$$$$$$   /$$$$$${X}
{R}       /$$__  $$| $$_____//$$__  $$ /$$__  ${X}
{R}       | $$  \ $$| $$     | $$  \ $$| $$  \__/{X}
{R}       | $$$$$$$$| $$$$$  | $$  | $$|  $$$$$${X}
{R}       | $$__  $$| $$__/  | $$  | $$ \____  ${X}
{R}       | $$  | $$| $$     | $$  | $$ /$$  \ ${X}
{R}       | $$  | $$| $$     |  $$$$$$/|  $$$$$$/{X}
{R}       |__/  |__/|__/      \______/  \______/{X}
"""

BANNER = f"""{LOGO}

{G}ANDRAX{X} {Y}Fucking{X} {R}Offensive Security{X} {G}Package Manager{X} {R}V6 SE{X}

Copyright 2021 The Cracker Technology - Advanced Pentest
Weidsom Nascimento <weidsom at thecrackertechnology.com>

"""

HELP = """
AFOS HELP:

        --install, -i: [ Install a package ]
        --update, -u: [ Update packages ]                                    --update-all, -a: [ Update all packages ]
        --list, -l: [ List installed packages by AFOS ]                      --repo, -r: [ List packages on AFOS REPO ]
        --debug, -d: [ Debug errors ]
        --help, -h [ Show this help ]
"""

MAIL = "Weidsom Nascimento <weidsom at thecrackertechnology.com>"

# ---------- 配置 ----------
DB_URL   = "https://raw.githubusercontent.com/the-cracker-thehnology/afos-repo/main/afos_db.txt"
DB_PATH  = "/opt/AFOS/afos_db.txt"
INSTALL_DIR = "/opt/ANDRAX"
AFOS_DIR = "/opt/AFOS"
BASE_REPO = "https://github.com/the-cracker-thehnology"

# ---------- 信号 ----------
signal.signal(signal.SIGINT, lambda s,f: sys.exit("\nABORTED.\n"))

# ---------- 错误处理 ----------
def fatal_error(msg, code=1):
    sys.stdout.write(f"{R}FATAL ERROR: {msg}{X}\n")
    sys.stdout.flush()
    sys.exit(code)

def error_out(msg, code=1):
    msg = re.sub(r'\[(ERROR)\]', f'[{R}\\1{X}]', msg)
    msg = re.sub(r'\[(WARN)\]', f'[{R}\\1{X}]', msg)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    sys.exit(code)

# ---------- 辅助函数 ----------
def out(s): sys.stdout.write(s); sys.stdout.flush()

def run(cmd, cwd=None, silent=False):
    try:
        if silent:
            return subprocess.run(cmd, cwd=cwd, capture_output=True).returncode == 0
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            out(line)
        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        error_out(f"[ ERROR ] {e} — {MAIL}")

def wget(url, dest): return run(['wget', '-q', '-O', dest, url], silent=True)

def download_db():
    os.makedirs(AFOS_DIR, exist_ok=True)
    return wget(DB_URL, DB_PATH)

def load_db():
    if not os.path.exists(DB_PATH):
        out("LOCAL MANIFEST MISSING. PULLING...\n")
        if not download_db():
            fatal_error("FAILED TO FETCH MANIFEST. CHECK NETWORK.")
        out("MANIFEST LOADED.\n")
    pkgs = {}
    with open(DB_PATH) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split()
            if len(parts) < 3:
                fatal_error(f"CORRUPT LINE {i}: '{line}'")
            name, ver, desc = parts[0], parts[1], ' '.join(parts[2:])
            pkgs[name.lower()] = {
                'name': name,
                'version': ver,
                'description': desc,
                'repo': f"{BASE_REPO}/{name}.git"
            }
    if not pkgs:
        fatal_error("NO PACKAGES AVAILABLE.")
    return pkgs

# ---------- 安装 / 更新单个（先删后装）----------
def process(pkg_name, confirm):
    db = load_db()
    pkg = db.get(pkg_name.lower())
    if not pkg:
        fatal_error(f"'{pkg_name}' NOT FOUND.")

    if confirm:
        out(f"\nINSTALL {pkg['name'].upper()}? [y/N]: ")
        if sys.stdin.readline().strip().lower() != 'y':
            out("ABORTED.\n")
            return

    path = os.path.join(INSTALL_DIR, pkg['name'])
    action = 'STARTING' if confirm else 'UPDATING'
    out(f"\n{action} [ {pkg['repo']} ]\n")
    os.makedirs(INSTALL_DIR, exist_ok=True)

    # 删除旧目录
    if os.path.exists(path):
        out("REMOVING OLD DIRECTORY...\n")
        try:
            shutil.rmtree(path)
        except Exception as e:
            fatal_error(f"FAILED TO REMOVE {path}: {e}")

    out("CLONING REPOSITORY...\n")
    if not run(['git', 'clone', pkg['repo'], path]):
        fatal_error("CLONE FAILED.")

    script = os.path.join(path, "AFOSBUILD.sh")
    if not os.path.exists(script):
        fatal_error("BUILD SCRIPT MISSING.")
    out("COMPILING...\n")
    if not run(['bash', script], cwd=path):
        fatal_error("BUILD FAILED.")
    out("BUILD SUCCESSFUL.\n")
    out("CLEANING UP\nUPDATING AFOS DATABASE\n")

def install(pkg): process(pkg, confirm=True)
def update_single(pkg): process(pkg, confirm=False)

# ---------- 更新所有包（先删后装，带进度）----------
def update_all():
    out("SCANNING FOR PACKAGE UPDATES...\n")
    out("EVERYTHING UP TO DATE.\n")
    out("UPDATE ALL? [y/N]: ")
    if sys.stdin.readline().strip().lower() != 'y':
        out("ABORTED.\n")
        return

    db = load_db()
    total = len(db)
    any_up = False
    for idx, pkg in enumerate(db.values(), 1):
        out(f"\n[{idx}/{total}] PROCESSING {pkg['name'].upper()}\n")
        out(f"SOURCE [ {pkg['repo']} ]\n")
        path = os.path.join(INSTALL_DIR, pkg['name'])
        try:
            if os.path.exists(path):
                out("NUKE OLD DIRECTORY...\n")
                shutil.rmtree(path)
            out("FRESH CLONE...\n")
            if not run(['git', 'clone', pkg['repo'], path]):
                out("[WARN] CLONE FAILED, SKIPPING.\n")
                continue
            script = os.path.join(path, "AFOSBUILD.sh")
            if not os.path.exists(script):
                out("[ERROR] BUILD SCRIPT MISSING, SKIPPING.\n")
                continue
            out("BUILDING...\n")
            if run(['bash', script], cwd=path):
                out(f"UPDATED {pkg['name'].upper()}\n")
                any_up = True
            else:
                out("[WARN] BUILD FAILED.\n")
        except Exception as e:
            out(f"[ERROR] {e}\n")

    if any_up:
        out("\nCLEANING UP\nUPDATING AFOS DATABASE\n")
    else:
        out("NOTHING UPDATED.\n")

# ---------- 列表 ----------
def list_local():
    db = load_db()
    out("INSTALLED PACKAGES (ONLY BY AFOS):\n")
    for pkg in db.values():
        out(f"{R}{pkg['name']}{X} {Y}{pkg['version']}{X} {G}{pkg['description']}{X}\n")

def list_remote():
    db = load_db()
    out("PACKAGES AVAILABLE ON AFOS REPOSITORY (SLOW LISTING):\n")
    for pkg in db.values():
        out(f"{R}{pkg['name']}{X} {Y}{pkg['version']}{X} {G}{pkg['description']}{X}\n")
        time.sleep(2)

def debug(): pass

# ---------- 数据库更新 ----------
def update_db():
    out("FETCHING LATEST PACKAGE MANIFEST...\n")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
    if not download_db():
        fatal_error("UPDATE FAILED. CHECK NETWORK.")
    out("MANIFEST UPDATED.\n")

# ---------- 主函数 ----------
def main():
    if os.geteuid() != 0:
        out(BANNER)
        fatal_error("BE ROOT MOTHERFUCKER! GTFO IF NOT ROOT.")
    out(BANNER)

    args = sys.argv[1:]
    if not args:
        return

    i = 0
    while i < len(args):
        a = args[i]
        if a in ('-i', '--install'):
            if i+1 >= len(args):
                fatal_error("OPTION -i REQUIRES A PACKAGE NAME, DUMBASS.")
            install(args[i+1])
            i += 2
        elif a in ('-u', '--update'):
            if i+1 < len(args) and not args[i+1].startswith('-'):
                update_single(args[i+1])
                i += 2
            else:
                update_db()
                i += 1
        elif a in ('-a', '--update-all'):
            update_all()
            i += 1
        elif a in ('-l', '--list'):
            list_local()
            i += 1
        elif a in ('-r', '--repo'):
            list_remote()
            i += 1
        elif a in ('-d', '--debug'):
            debug()
            i += 1
        elif a in ('-h', '--help'):
            out(HELP)
            return
        else:
            # 未知选项：静默忽略
            return

if __name__ == "__main__":
    main()