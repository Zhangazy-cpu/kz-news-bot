import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SITE = ROOT / "site"
VIDEO = ROOT / "video"
RUN_PUBLIC = VIDEO / "public" / "run"
STATE_FILE = ROOT / "state" / "posted.json"


def load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def log(*a):
    print("[bot]", *a, flush=True)
