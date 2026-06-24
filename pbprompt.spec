# -*- mode: python ; coding: utf-8 -*-

import certifi
import glob
import importlib.util
import os
import subprocess
import sys


def _ssl_binaries():
    """Return (src, dest) pairs for OpenSSL shared libs needed by _ssl / _hashlib.

    PyInstaller skips system libs by default; on conda builds the libs live in
    $CONDA_PREFIX/lib and are equally invisible.  We resolve the actual paths
    via ``ldd`` (Linux/macOS) or by scanning %CONDA_PREFIX%\\Library\\bin
    (Windows) so the frozen executable carries its own OpenSSL.
    """
    result = []

    if sys.platform == "win32":
        conda_prefix = os.environ.get("CONDA_PREFIX", "")
        bin_dir = os.path.join(conda_prefix, "Library", "bin") if conda_prefix else ""
        for pat in ["libssl-*.dll", "libcrypto-*.dll"]:
            for f in glob.glob(os.path.join(bin_dir, pat)):
                result.append((f, "."))
        return result

    # Linux / macOS — follow the actual link chain from _ssl and _hashlib
    seen = set()
    for mod in ("_ssl", "_hashlib"):
        spec = importlib.util.find_spec(mod)
        if not (spec and spec.origin):
            continue
        try:
            ldd_out = subprocess.check_output(["ldd", spec.origin], text=True)
        except Exception:
            continue
        for line in ldd_out.splitlines():
            if "=>" not in line:
                continue
            name_part, path_part = line.split("=>", 1)
            name = name_part.strip().split()[0] if name_part.strip() else ""
            if not ("libssl" in name or "libcrypto" in name):
                continue
            path = path_part.strip().split()[0]
            if path and os.path.isfile(path) and path not in seen:
                seen.add(path)
                result.append((path, "."))

    return result


a = Analysis(
    ["src/pbprompt/__main__.py"],
    pathex=[],
    binaries=_ssl_binaries(),
    datas=[
        ("locales", "locales"),
        ("src/pbprompt/icons", "pbprompt/icons"),
        (certifi.where(), "certifi"),
    ],
    hiddenimports=["certifi", "ssl", "_ssl", "_hashlib"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["hooks/rthook_ssl.py"],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pbprompt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
