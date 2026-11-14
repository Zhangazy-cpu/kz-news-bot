"""Публикация Reels через официальный Instagram API (вход через Instagram)."""
import time

import requests

from . import env, log

VER = env("IG_API_VERSION", "v25.0")
HOSTS = [f"https://graph.instagram.com/{VER}", f"https://graph.facebook.com/{VER}"]
_api: list[str] = []  # хост, который принял токен


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
    """Определяет, какой хост Meta принимает токен, и возвращает {'id','username'} аккаунта Instagram."""
    from . import load_config

    ig_id = env("IG_USER_ID") or str(load_config()["account"].get("ig_user_id", ""))
    errors = []
    for host in HOSTS:
        try:
            if "instagram.com" in host:
                d = _check(requests.get(f"{host}/me", params={"fields": "user_id,username", "access_token": _token()}, timeout=30))
                d["id"] = d.get("user_id") or d.get("id")
            else:
                d = _check(requests.get(f"{host}/{ig_id}", params={"fields": "id,username", "access_token": _token()}, timeout=30))
            _api[:] = [host]
            log(f"токен принят: {host.split('/')[2]}, аккаунт @{d.get('username')}")
            return d
        except Exception as e:  # noqa: BLE001
            errors.append(f"{host.split('/')[2]}: {str(e)[:200]}")
    raise RuntimeError("Токен Instagram не подошёл: " + " | ".join(errors))


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
    ig_id = ig["id"]
    API = _api[0]
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


def check() -> None:
    d = me()
    lim = _check(requests.get(f"{_api[0]}/{d['id']}/content_publishing_limit", params={"access_token": _token()}, timeout=30))
    log("лимит публикаций:", lim)


def refresh_token() -> str:
    """Продлевает долгосрочный токен ещё на 60 дней."""
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": _token()},
        timeout=30,
    )
    if r.status_code != 200:  # токен системного пользователя не истекает — продлевать не нужно
        log("продление не требуется или недоступно:", r.text[:200])
        return ""
    return _check(r)["access_token"]
