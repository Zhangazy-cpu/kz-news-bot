"""Очередь готовых роликов. Хранится как файлы в релизе «queue» на GitHub (не раздувает репозиторий)."""
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import env, log

TAG = "queue"


def _gh(*args: str, check=True) -> subprocess.CompletedProcess:
    repo = env("GITHUB_REPOSITORY")
    cmd = ["gh", *args] + (["-R", repo] if repo else [])
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _ensure() -> None:
    if _gh("release", "view", TAG, check=False).returncode != 0:
        _gh("release", "create", TAG, "--title", "Очередь роликов", "--notes",
            "Готовые ролики, ждущие публикации. Файлы удаляются после выкладки в Instagram.", "--prerelease")


def items() -> list[dict]:
    """Метаданные всех роликов в очереди, от старых к новым."""
    _ensure()
    with tempfile.TemporaryDirectory() as d:
        r = _gh("release", "download", TAG, "-p", "*.json", "-D", d, "--clobber", check=False)
        if r.returncode != 0 and "no assets" not in (r.stderr + r.stdout).lower():
            log("очередь: не удалось скачать список:", r.stderr.strip()[:200])
        metas = []
        for p in Path(d).glob("*.json"):
            try:
                metas.append(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
    return sorted(metas, key=lambda m: m.get("created_at", ""))


def age_hours(meta: dict) -> float:
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(meta["created_at"])).total_seconds() / 3600
    except (KeyError, ValueError):
        return 999.0


def add(mp4: Path, cover: Path, meta: dict) -> None:
    _ensure()
    slug = meta["slug"]
    with tempfile.TemporaryDirectory() as d:
        files = []
        for src, name in ((mp4, f"{slug}.mp4"), (cover, f"{slug}.jpg")):
            dst = Path(d) / name
            dst.write_bytes(Path(src).read_bytes())
            files.append(str(dst))
        mj = Path(d) / f"{slug}.json"
        mj.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        files.append(str(mj))  # json последним: его наличие = ролик загружен полностью
        _gh("release", "upload", TAG, *files, "--clobber")
    log(f"в очередь добавлен: {slug}")


def download(slug: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    _gh("release", "download", TAG, "-p", f"{slug}.*", "-D", str(dest), "--clobber")


def remove(slug: str) -> None:
    for ext in ("json", "mp4", "jpg"):
        _gh("release", "delete-asset", TAG, f"{slug}.{ext}", "-y", check=False)
    log(f"из очереди удалён: {slug}")
