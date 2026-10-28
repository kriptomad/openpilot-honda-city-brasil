"""hp_common.py - shared guard/backup/log helpers for all HybridPanda_v2 scripts.

Every script imports this module and MUST route every write through guarded_path()/backup_before_write().
Rules implemented (prompt 0x00 §2-3, Diretriz 6):
  * OUTPUT_ROOT / ORIGINAL_ROOT constants
  * assert_inside_output(path): resolves symlinks and '..'; refuses writes outside OUTPUT_ROOT or inside ORIGINAL_ROOT
  * backup_before_write(path): dated copy into 99_BACKUPS before any overwrite
  * JsonLog: structured log written to 06_REPORTS
  * DRY_RUN flag honoured by write helpers
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------- constants (edit here only)
OUTPUT_ROOT = Path(r"C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616")
ORIGINAL_ROOT = Path(r"C:\Users\costabr\Downloads\openpilot\OpenpilotHardware-main\OpenpilotHardware-main")
REFERENCE_ROOT = OUTPUT_ROOT / "02_REFERENCE"
BACKUP_DIR = OUTPUT_ROOT / "99_BACKUPS"
REPORT_DIR = OUTPUT_ROOT / "06_REPORTS"
KICAD_BIN = Path(r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin")
KICAD_CLI = KICAD_BIN / "kicad-cli.exe"
# ----------------------------------------------------------------

DRY_RUN = False


class GuardError(RuntimeError):
    pass


def _real(p: Path) -> Path:
    return Path(os.path.realpath(str(p)))


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def assert_inside_output(path: os.PathLike | str) -> Path:
    """Return the resolved path if it is a legal write target, else raise GuardError."""
    rp = _real(Path(path))
    out = _real(OUTPUT_ROOT)
    orig = _real(ORIGINAL_ROOT)
    if _is_inside(rp, orig):
        raise GuardError(f"REFUSED: write inside ORIGINAL_ROOT: {rp}")
    if not _is_inside(rp, out):
        raise GuardError(f"REFUSED: write outside OUTPUT_ROOT: {rp}")
    if _is_inside(rp, _real(REFERENCE_ROOT)):
        raise GuardError(f"REFUSED: write inside read-only 02_REFERENCE: {rp}")
    return rp


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def backup_before_write(path: os.PathLike | str, tag: str = "") -> Path | None:
    """Copy an existing file into 99_BACKUPS/<timestamp>_<tag>/<relative path>. Returns backup path or None."""
    rp = assert_inside_output(path)
    if not rp.exists():
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rel = rp.relative_to(_real(OUTPUT_ROOT))
    dest = BACKUP_DIR / f"{stamp}{('_' + tag) if tag else ''}" / rel
    if DRY_RUN:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rp, dest)
    return dest


def guarded_write_text(path: os.PathLike | str, text: str, tag: str = "", encoding: str = "utf-8") -> Path:
    rp = assert_inside_output(path)
    backup_before_write(rp, tag)
    if not DRY_RUN:
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(text, encoding=encoding, newline="\n")
    return rp


class JsonLog:
    """Structured JSON log stored in 06_REPORTS/<name>.json (list of events + summary)."""

    def __init__(self, name: str):
        self.path = REPORT_DIR / f"{name}.json"
        self.events: list[dict] = []
        self.t0 = time.time()
        self.meta = {"script": name, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "dry_run": DRY_RUN,
                     "output_root": str(OUTPUT_ROOT), "python": sys.version.split()[0]}

    def add(self, level: str, msg: str, **kw):
        ev = {"t": round(time.time() - self.t0, 3), "level": level, "msg": msg}
        ev.update(kw)
        self.events.append(ev)
        print(f"[{level}] {msg}" + (f" {kw}" if kw else ""))

    def info(self, msg, **kw): self.add("INFO", msg, **kw)
    def warn(self, msg, **kw): self.add("WARN", msg, **kw)
    def error(self, msg, **kw): self.add("ERROR", msg, **kw)

    def save(self, **summary):
        assert_inside_output(self.path)
        doc = {"meta": self.meta, "summary": summary, "events": self.events,
               "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"log -> {self.path}")
        return self.path


def std_argparser(desc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--dry-run", action="store_true", help="do not write anything; report what would be done")
    return ap


def apply_args(args) -> None:
    global DRY_RUN
    DRY_RUN = bool(getattr(args, "dry_run", False))


def selftest() -> None:
    """Prove the guard: OUTPUT_ROOT ok, ORIGINAL refused, outside refused, '..' escape refused, 02_REFERENCE refused."""
    ok = assert_inside_output(OUTPUT_ROOT / "06_REPORTS" / "x.txt")
    assert ok
    for bad in (ORIGINAL_ROOT / "a.txt", Path(r"C:\Windows\Temp\x.txt"),
                OUTPUT_ROOT / ".." / "HybridPanda_v1" / "x.txt", REFERENCE_ROOT / "panda" / "x"):
        try:
            assert_inside_output(bad)
        except GuardError:
            continue
        raise AssertionError(f"guard failed for {bad}")
    print("hp_common selftest OK")


if __name__ == "__main__":
    selftest()
