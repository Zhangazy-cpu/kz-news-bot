"""Сбор свежих новостей из RSS открытых казахстанских СМИ."""
import html
import re
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import quote, urljoin

import feedparser
import requests

from . import log

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _norm(s: str) -> str:
    return re.sub(r"[^\w ]", "", s.lower()).strip()


def similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio() > 0.62


def _get(url: str, timeout=20) -> requests.Response | None:
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200 and r.content:
            return r
    except requests.RequestException:
        pass
    return None


def _discover_feed(site: str) -> str | None:
    r = _get(site)
    if not r:
        return None
    m = re.search(r'<link[^>]+type="application/(?:rss|atom)\+xml"[^>]*>', r.text, re.I)
    if not m:
        return None
    href = re.search(r'href="([^"]+)"', m.group(0))
    return urljoin(site, html.unescape(href.group(1))) if href else None


def _parse(content: bytes, source: str, max_age_h: float) -> list[dict]:
    feed = feedparser.parse(content)
    now = time.time()
    out = []
    for e in feed.entries[:60]:
        ts = e.get("published_parsed") or e.get("updated_parsed")
        age_h = (now - time.mktime(ts)) / 3600 if ts else 0
        if ts and age_h > max_age_h:
            continue
        title = _clean(e.get("title", ""))
        if not title:
            continue
        out.append(
            {
                "title": title,
                "summary": _clean(e.get("summary", ""))[:600],
                "link": e.get("link", ""),
                "source": source,
                "age_h": round(max(age_h, 0), 1),
            }
        )
    return out


def fetch_candidates(cfg: dict, posted: list[dict]) -> list[dict]:
    ncfg = cfg["news"]
    max_age = ncfg.get("max_age_hours", 20)
    items: list[dict] = []
    for f in ncfg["feeds"]:
        r = _get(f["url"])
        if r is None or not feedparser.parse(r.content).entries:
            alt = _discover_feed(f.get("site", "")) if f.get("site") else None
            r = _get(alt) if alt else None
        if r is None:
            log(f"лента недоступна: {f['name']} ({f['url']})")
            continue
        got = _parse(r.content, f["name"], max_age)
        log(f"{f['name']}: {len(got)} свежих")
        items += got

    if len(items) < 8 and ncfg.get("google_news_fallback", True):
        for q in ["Қазақстан", "Казахстан"]:
            url = f"https://news.google.com/rss/search?q={quote(q)}+when:1d&hl=ru&gl=KZ&ceid=KZ:ru"
            r = _get(url)
            if r:
                got = _parse(r.content, "Google News", max_age)
                for g in got:
                    # заголовок Google News: "Текст - Источник"
                    if " - " in g["title"]:
                        g["title"], g["source"] = g["title"].rsplit(" - ", 1)
                    g["google"] = True
                items += got
                log(f"Google News ({q}): {len(got)}")

    # фильтры: стоп-слова, уже опубликованное, дубликаты между сайтами
    stop = [w.lower() for w in cfg.get("safety", {}).get("skip_keywords", [])]
    posted_titles = [p.get("source_title", "") for p in posted[-120:]]
    posted_links = {p.get("link") for p in posted}
    result: list[dict] = []
    for it in items:
        text = (it["title"] + " " + it["summary"]).lower()
        if any(w in text for w in stop):
            continue
        if it["link"] in posted_links or any(similar(it["title"], t) for t in posted_titles if t):
            continue
        if any(similar(it["title"], r["title"]) for r in result):
            continue
        result.append(it)
    log(f"кандидатов после фильтров: {len(result)}")
    result.sort(key=lambda x: x["age_h"])  # сначала самые свежие
    result = result[:60]
    for i, it in enumerate(result):
        it["id"] = i
    return result


def article_text(item: dict) -> str:
    """Полный текст статьи (если сайт отдаёт), иначе анонс из RSS."""
    if item.get("google") or not item.get("link"):
        return item["summary"]
    try:
        import trafilatura

        r = _get(item["link"], timeout=25)
        if r:
            txt = trafilatura.extract(r.text, include_comments=False, include_tables=False) or ""
            if len(txt) > 200:
                return txt[:7000]
    except Exception as e:  # noqa: BLE001
        log("не удалось извлечь текст:", e)
    return item["summary"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
