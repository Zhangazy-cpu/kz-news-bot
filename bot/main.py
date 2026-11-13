"""Оркестратор бота.

  python -m bot.main build     — найти новость, написать сценарий, озвучить, отрендерить (out/, site/)
  python -m bot.main publish   — выложить готовый ролик в Instagram (нужен PAGES_URL)
  python -m bot.main demo      — отрендерить пробный ролик из bot/demo_script.json (без ИИ)
  python -m bot.main refresh   — продлить токен Instagram (печатает новый токен)
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import OUT, ROOT, RUN_PUBLIC, SITE, env, load_config, log
from . import instagram, llm, media, news, prompts, state, tts

TYPES = {"hook", "number", "list", "timeline", "flow", "statement", "photo", "compare", "outro"}
MONTHS = ["қаңтар", "ақпан", "наурыз", "сәуір", "мамыр", "маусым", "шілде", "тамыз", "қыркүйек", "қазан", "қараша", "желтоқсан"]


def kz_date(dt: datetime) -> str:
    return f"{dt.day} {MONTHS[dt.month - 1]} {dt.year}"


def gh_output(**kw) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            for k, v in kw.items():
                f.write(f"{k}={v}\n")


def sanitize(script: dict) -> list[dict]:
    scenes = [s for s in script.get("scenes", []) if s.get("type") in TYPES and (s.get("narration") or "").strip()]
    for s in scenes:
        if s.get("highlight") and s["highlight"] not in (s.get("title") or ""):
            s.pop("highlight")
        for k in ("items", "points", "steps"):
            if k in s and not isinstance(s[k], list):
                s.pop(k)
        s.pop("bg", None)
    if not scenes or scenes[-1]["type"] != "outro":
        scenes.append({"type": "outro", "title": "Жазылыңыз", "narration": "Күн сайынғы жаңалықтар үшін парақшаға жазылыңыз."})
    if len(scenes) > 10:
        scenes = scenes[:9] + [scenes[-1]]
    return scenes


def fit_length(scenes: list[dict], max_s: float) -> list[dict]:
    while sum(s["duration"] for s in scenes) > max_s and len(scenes) > 4:
        scenes.pop(-2)  # убираем предпоследнюю содержательную сцену
    return scenes


def build_caption(script: dict, item: dict, cfg: dict) -> str:
    tags = []
    for t in script.get("hashtags", []) + cfg["posting"].get("hashtags", []):
        t = "#" + re.sub(r"[#\s]", "", t)
        if t.lower() not in [x.lower() for x in tags]:
            tags.append(t)
    cap = (script.get("caption") or script.get("headline", "")).strip()
    cap += f"\n\nДереккөз: {item['source']}"
    cap += "\n\n" + " ".join(tags[:12])
    return cap[:2150]


def produce(scenes: list[dict], cfg: dict, source: str, allow_silent=False) -> tuple[Path, Path, dict]:
    acc = cfg["account"]
    media.reset_run_dir()
    media.fetch_images(scenes)
    voice = tts.synthesize(scenes, acc["voice"], acc.get("rate", "+0%"), RUN_PUBLIC, allow_silent=allow_silent)
    n = len(scenes)
    scenes = fit_length(scenes, cfg["posting"].get("max_video_seconds", 75))
    if voice and len(scenes) != n:  # после обрезки сцен пересобираем общий трек
        voice = tts.synthesize(scenes, acc["voice"], acc.get("rate", "+0%"), RUN_PUBLIC)
    props = {
        "handle": acc["handle"],
        "brand": acc.get("brand", "KZ"),
        "source": source,
        "audio": "run/voice.mp3" if voice else None,
        "scenes": scenes,
    }
    mp4, cover = media.render(props, OUT)
    return mp4, cover, props


def cmd_build(dry=False) -> None:
    cfg = load_config()
    posted = state.load()
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.rmtree(SITE, ignore_errors=True)
    OUT.mkdir(parents=True)
    SITE.mkdir(parents=True)

    cands = news.fetch_candidates(cfg, posted)
    if not cands:
        log("нет новых новостей — пропускаю запуск")
        gh_output(has_reel="false")
        return

    recent = [p.get("headline", p.get("source_title", "")) for p in posted]
    today = kz_date(datetime.now(timezone(timedelta(hours=5))))
    tried = set()
    item, script, chosen = None, {}, False
    for _ in range(3):  # до трёх попыток найти пригодную новость
        pool = [c for c in cands if c["id"] not in tried]
        if not pool:
            break
        pick = llm.ask_json(prompts.SELECT_SYSTEM, prompts.select_user(pool, recent))
        cid = int(pick.get("id", -1))
        if cid < 0:
            break
        tried.add(cid)
        item = next((c for c in cands if c["id"] == cid), None)
        if not item:
            continue
        log(f"выбрана: [{item['source']}] {item['title']} — {pick.get('reason', '')}")
        text = news.article_text(item)
        script = llm.ask_json(prompts.WRITE_SYSTEM, prompts.write_user(item, text, today))
        checked = llm.ask_json(prompts.VERIFY_SYSTEM, prompts.verify_user(text, script))
        if checked.get("publishable") is False:
            log("редактор-проверка забраковала новость:", checked.get("issues"))
            continue
        if checked.get("scenes"):
            script = checked
        log("правки проверки:", script.get("issues", []))
        chosen = True
        break
    if not chosen or not script.get("scenes"):
        log("подходящей новости не нашлось — пропускаю")
        gh_output(has_reel="false")
        return

    scenes = sanitize(script)
    mp4, cover, props = produce(scenes, cfg, item["source"])
    slug = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    shutil.copy(mp4, SITE / f"{slug}.mp4")
    shutil.copy(cover, SITE / f"{slug}.jpg")
    (SITE / "index.html").write_text("<meta charset=utf-8><p>KZ news bot: OK</p>", encoding="utf-8")
    meta = {
        "slug": slug,
        "headline": script.get("headline", item["title"]),
        "caption": build_caption(script, item, cfg),
        "source": item["source"],
        "source_title": item["title"],
        "link": item["link"],
        "seconds": round(sum(s["duration"] for s in props["scenes"]), 1),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"готово: {meta['seconds']} с — {meta['headline']}")
    gh_output(has_reel="true")


def cmd_publish() -> None:
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))
    base = env("PAGES_URL").rstrip("/")
    if not base:
        raise RuntimeError("PAGES_URL не задан")
    video_url = f"{base}/{meta['slug']}.mp4"
    cover_url = f"{base}/{meta['slug']}.jpg"
    instagram.wait_url(video_url)
    res = instagram.publish_reel(video_url, cover_url, meta["caption"])
    state.add({k: meta[k] for k in ("headline", "source", "source_title", "link")} | res)


def cmd_demo() -> None:
    cfg = load_config()
    script = json.loads((ROOT / "bot" / "demo_script.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    scenes = sanitize(script)
    mp4, cover, props = produce(scenes, cfg, script.get("source", ""), allow_silent=True)
    log("демо:", mp4, f"{sum(s['duration'] for s in props['scenes']):.1f} с")


def cmd_refresh() -> None:
    new = instagram.refresh_token()
    print(f"::add-mask::{new}")
    Path(os.environ.get("NEW_TOKEN_FILE", "/tmp/new_token")).write_text(new)
    log("токен продлён на 60 дней")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"build": cmd_build, "publish": cmd_publish, "demo": cmd_demo, "refresh": cmd_refresh}[cmd]()
