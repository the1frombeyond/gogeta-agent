"""
Comprehensive rename: gogeta/gogeta -> gogeta (files, dirs, and content).
"""
import os
import re
import shutil

ROOT = r"C:\Users\the1frombeyond\Downloads\gogeta"
os.chdir(ROOT)

TEXT_EXTS = {
    ".py", ".toml", ".md", ".yaml", ".yml", ".json", ".sh", ".ps1",
    ".cmd", ".txt", ".cfg", ".ini", ".env", ".service", ".nix", ".rb",
    ".ts", ".tsx", ".html", ".css", ".js", ".jsx", ".manifest", ".desktop",
    ".svg", ".conf", ".yml.example",
}
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "target", "dist", "build",
    ".venv", "venv", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "genome", "lifeline", "gogeta",
}

def is_text(p):
    return os.path.splitext(p)[1].lower() in TEXT_EXTS

def should_skip(dirpath):
    parts = os.path.relpath(dirpath, ROOT).replace("\\", "/").split("/")
    return any(p in SKIP_DIRS for p in parts) or parts[0] in SKIP_DIRS

def walk():
    for d, dirs, files in os.walk(ROOT):
        if should_skip(d):
            continue
        for f in files:
            yield os.path.join(d, f)

def replace_in(fpath, old, new):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            c = f.read()
    except Exception:
        return False
    if old not in c:
        return False
    nc = c.replace(old, new)
    if nc == c:
        return False
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(nc)
    return True

CONTENT_REPLACEMENTS = [
    ("gogeta_bootstrap", "gogeta_bootstrap"),
    ("gogeta_constants", "gogeta_constants"),
    ("gogeta_logging", "gogeta_logging"),
    ("gogeta_state", "gogeta_state"),
    ("gogeta_time", "gogeta_time"),
    ("gogeta_cli", "gogeta_cli"),
    ("GOGETA_HOME", "GOGETA_HOME"),
    ("~/.gogeta", "~/.gogeta"),
    ("%LOCALAPPDATA%\\gogeta", "%LOCALAPPDATA%\\gogeta"),
    ("gogeta_bootstrap", "gogeta_bootstrap"),
    ("gogeta_constants", "gogeta_constants"),
    ("gogeta_logging", "gogeta_logging"),
    ("gogeta_state", "gogeta_state"),
    ("gogeta_time", "gogeta_time"),
    ("gogeta_cli", "gogeta_cli"),
    ("GOGETA_HOME", "GOGETA_HOME"),
    ("~/.gogeta", "~/.gogeta"),
    ("get_gogeta_home", "get_gogeta_home"),
    ("_gogeta_home", "_gogeta_home"),
    ("Gogeta", "Gogeta"),
    ("Gogeta", "Gogeta"),
    ("GOGETA_", "GOGETA_"),
    ("GOGETA_", "GOGETA_"),
    ("-gogeta", "-gogeta"),
    ("gogeta-", "gogeta-"),
    ("gogeta", "gogeta"),
    ("gogeta", "gogeta"),
    ("GOGETA", "GOGETA"),
    ("GOGETA", "GOGETA"),
]

def rename_file_or_dir(old_path, new_name):
    parent = os.path.dirname(old_path)
    new_path = os.path.join(parent, new_name)
    if old_path == new_path or os.path.exists(new_path):
        return False
    try:
        os.rename(old_path, new_path)
        return True
    except Exception as e:
        print(f"  SKIP {os.path.basename(old_path)}: {e}")
        return False

def rename_gogeta_gogeta_names():
    renamed_files = 0
    renamed_dirs = 0
    all_dirs = []
    all_files = []
    for d, dirs, files in os.walk(ROOT):
        if should_skip(d):
            continue
        all_dirs.append(d)
        for f in files:
            all_files.append(os.path.join(d, f))
    for fpath in all_files:
        fname = os.path.basename(fpath)
        lower = fname.lower()
        new_name = fname
        for search, replace in [("gogeta","gogeta"),("gogeta","gogeta")]:
            if search in lower:
                idx = lower.index(search)
                prefix = new_name[:idx]
                suffix = new_name[idx+len(search):]
                orig = fname[idx:idx+len(search)]
                if orig.isupper():
                    new_base = replace.upper()
                elif orig[0].isupper() and orig[1:].islower():
                    new_base = replace.capitalize()
                else:
                    new_base = replace
                new_name = prefix + new_base + suffix
                lower = new_name.lower()
        if new_name != fname:
            if rename_file_or_dir(fpath, new_name):
                print(f"  RENAMED FILE: {fname} -> {new_name}")
                renamed_files += 1
    for dpath in reversed(all_dirs):
        if os.path.abspath(dpath) == os.path.abspath(ROOT):
            continue
        dname = os.path.basename(dpath)
        if dname in SKIP_DIRS:
            continue
        lower = dname.lower()
        new_name = dname
        for search, replace in [("gogeta","gogeta"),("gogeta","gogeta")]:
            if search in lower:
                idx = lower.index(search)
                prefix = new_name[:idx]
                suffix = new_name[idx+len(search):]
                orig = dname[idx:idx+len(search)]
                if orig.isupper():
                    new_base = replace.upper()
                elif orig[0].isupper() and orig[1:].islower():
                    new_base = replace.capitalize()
                else:
                    new_base = replace
                new_name = prefix + new_base + suffix
                lower = new_name.lower()
        if new_name != dname:
            if rename_file_or_dir(dpath, new_name):
                print(f"  RENAMED DIR:  {dname} -> {new_name}")
                renamed_dirs += 1
    return renamed_files, renamed_dirs

def phase_delete_stale():
    print("=" * 60)
    print("PHASE 0: Delete stale gogeta_* files/dirs")
    print("=" * 60)
    targets = [
        "gogeta_bootstrap.py", "gogeta_constants.py", "gogeta_logging.py",
        "gogeta_state.py", "gogeta_time.py", "gogeta", "setup-gogeta.sh",
        "gogeta-already-has-routines.md",
    ]
    for t in targets:
        p = os.path.join(ROOT, t)
        try:
            if os.path.isfile(p) or os.path.islink(p):
                os.remove(p)
                print(f"  DELETED {t}")
        except FileNotFoundError:
            pass
    for d in ["gogeta_cli", os.path.join("tests", "gogeta_cli")]:
        p = os.path.join(ROOT, d)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
                print(f"  DELETED {d}/")
        except FileNotFoundError:
            pass
    old_migrate = os.path.join(ROOT, "scripts", "rename_gogeta_to_gogeta.ps1")
    try:
        if os.path.isfile(old_migrate):
            os.remove(old_migrate)
            print(f"  DELETED scripts/rename_gogeta_to_gogeta.ps1")
    except FileNotFoundError:
        pass
    print()

def phase_rename_files():
    print("=" * 60)
    print("PHASE 1: Rename files/dirs with gogeta/gogeta in name")
    print("=" * 60)
    nf, nd = rename_gogeta_gogeta_names()
    print(f"  -> {nf} files, {nd} dirs renamed\n")

def phase_replace_content():
    print("=" * 60)
    print("PHASE 2: Replace gogeta/gogeta -> gogeta in file contents")
    print("=" * 60)
    stats = {old: 0 for old, _ in CONTENT_REPLACEMENTS}
    for fpath in walk():
        if not is_text(fpath):
            continue
        for old, new in CONTENT_REPLACEMENTS:
            if replace_in(fpath, old, new):
                stats[old] += 1
    for old, c in stats.items():
        if c:
            print(f"  '{old}' -> replaced in {c} file(s)")
    print()

def run():
    phase_delete_stale()
    phase_rename_files()
    phase_replace_content()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

if __name__ == "__main__":
    run()
