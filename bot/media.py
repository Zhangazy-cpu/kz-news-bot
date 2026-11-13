"""Картинки (необязательно, бесплатный Pexels) и рендер видео через Remotion."""
import json
import shutil
import subprocess
from pathlib import Path

import requests

from . import RUN_PUBLIC, VIDEO, env, log


def fetch_images(scenes: list[dict]) -> None:
    """Если задан PEXELS_API_KEY — подбираем нейтральные стоковые фото по imageQuery. Иначе сцены без фото."""
    key = env("PEXELS_API_KEY")
    for i, sc in enumerate(scenes):
        q = sc.pop("imageQuery", None)
        sc.pop("image", None)
        if not (key and q):
            continue
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": q, "orientation": "landscape", "per_page": 3},
                headers={"Authorization": key},
                timeout=20,
            )
            photos = r.json().get("photos", [])
            if not photos:
                continue
            img = requests.get(photos[0]["src"]["large"], timeout=30).content
            name = f"img{i}.jpg"
            (RUN_PUBLIC / name).write_bytes(img)
            sc["image"] = f"run/{name}"
        except Exception as e:  # noqa: BLE001
            log("картинка не загрузилась:", q, e)


def _npx(args: list[str]) -> None:
    cmd = ["npx", "--no-install", "remotion", *args, "--log=warn"]
    chrome = env("CHROME_PATH")
    if chrome:
        cmd.append(f"--browser-executable={chrome}")
    subprocess.run(cmd, cwd=VIDEO, check=True)


def render(props: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    props_path = out_dir / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    mp4 = out_dir / "reel.mp4"
    cover = out_dir / "cover.jpg"
    _npx(["render", "src/index.ts", "NewsReel", str(mp4), f"--props={props_path}", "--audio-codec=aac", "--crf=20"])
    _npx(["still", "src/index.ts", "NewsReel", str(cover), f"--props={props_path}", "--frame=40", "--image-format=jpeg"])
    return mp4, cover


def reset_run_dir() -> None:
    shutil.rmtree(RUN_PUBLIC, ignore_errors=True)
    RUN_PUBLIC.mkdir(parents=True, exist_ok=True)
