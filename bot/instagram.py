"""Публикация Reels через официальный Instagram API (вход через Instagram)."""
import time

import requests

from . import env, log

API = "https://graph.instagram.com/" + env("IG_API_VERSION", "v25.0")


def _token() -> str:
    t = env("IG_ACCESS_TOKEN")
    if not t:
        raise RuntimeError("Нет секрета IG_ACCESS_TOKEN")
    return t


def _check(r: requests.Response) -> dict:
    data = r.json() if r.content else {}
    if r.status_code != 200 or "error" in data:
        raise RuntimeError(f"Instagram API: {r.status_code} {data}")
    return data


def me() -> dict:
    return _check(requests.get(f"{API}/me", params={"fields": "user_id,username", "access_token": _token()}, timeout=30))


def wait_url(url: str, minutes=8) -> None:
    """Ждём, пока GitHub Pages начнёт отдавать файл."""
    for _ in range(minutes * 6):
        try:
            if requests.head(url, timeout=15, allow_redirects=True).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(10)
    raise RuntimeError(f"Файл не появился по адресу {url}")


def publish_reel(video_url: str, cover_url: str | None, caption: str) -> dict:
    ig = me()
    ig_id = ig.get("user_id") or ig.get("id")
    log(f"публикую в @{ig.get('username')}…")
    data = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true", "access_token": _token()}
    if cover_url:
        data["cover_url"] = cover_url
    cid = _check(requests.post(f"{API}/{ig_id}/media", data=data, timeout=60))["id"]

    for _ in range(60):  # до 10 минут обработки видео
        st = _check(requests.get(f"{API}/{cid}", params={"fields": "status_code,status", "access_token": _token()}, timeout=30))
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram не принял видео: {st}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram слишком долго обрабатывает видео")

    media_id = _check(requests.post(f"{API}/{ig_id}/media_publish", data={"creation_id": cid, "access_token": _token()}, timeout=60))["id"]
    info = {}
    try:
        info = _check(requests.get(f"{API}/{media_id}", params={"fields": "permalink", "access_token": _token()}, timeout=30))
    except Exception:  # noqa: BLE001
        pass
    log("опубликовано:", info.get("permalink", media_id))
    return {"ig_media_id": media_id, "permalink": info.get("permalink", "")}


def refresh_token() -> str:
    """Продлевает долгосрочный токен ещё на 60 дней."""
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": _token()},
        timeout=30,
    )
    return _check(r)["access_token"]
