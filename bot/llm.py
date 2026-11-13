"""Обращение к ИИ: бесплатный Gemini (по умолчанию) или Claude (если задан ключ)."""
import json
import re
import time

import requests

from . import env, log

GEMINI_MODELS = [m for m in [env("GEMINI_MODEL"), "gemini-flash-latest", "gemini-3.8-flash", "gemini-flash-lite-latest"] if m]


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
_BAD = ("image", "tts", "audio", "live", "embedding", "thinking", "computer", "robotics")
_models_cache: list[str] = []
_dead: set[str] = set()


def _gemini_models(key: str) -> list[str]:
    """Список доступных моделей Flash: сначала предпочтительные, потом остальные (новые — первыми)."""
    if _models_cache:
        return [m for m in _models_cache if m not in _dead]
    found = []
    try:
        r = requests.get(f"{GEMINI_URL}/models", params={"pageSize": 200}, headers={"x-goog-api-key": key}, timeout=30)
        for m in r.json().get("models", []):
            name = m["name"].split("/", 1)[-1]
            if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in name and not any(b in name for b in _BAD):
                found.append(name)
    except Exception as e:  # noqa: BLE001
        log("не удалось получить список моделей Gemini:", e)
    pref = [m for m in GEMINI_MODELS if m != "gemini-2.5-flash"]
    stable = sorted((m for m in found if "preview" not in m and "exp" not in m), reverse=True)
    rest = sorted((m for m in found if m not in stable), reverse=True)
    full = [m for m in stable if "lite" not in m] + [m for m in stable if "lite" in m] + rest
    order = []
    for m in pref + full:
        if m not in order:
            order.append(m)
    _models_cache.extend(order)
    log("модели Gemini:", ", ".join(order[:8]))
    return order


class LLMBusy(RuntimeError):
    """Серверы ИИ перегружены — запуск можно спокойно пропустить."""


def _gemini(system: str, user: str) -> str:
    key = env("GEMINI_API_KEY")
    last = None
    busy = False
    for rnd in range(5):  # до 5 кругов по моделям — перегрузка у Google обычно проходит за минуты
        for model in _gemini_models(key)[:6]:
            try:
                r = requests.post(
                f"{GEMINI_URL}/models/{model}:generateContent",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.55},
                },
                timeout=150,
                )
            except requests.RequestException as e:
                last = f"{model}: {type(e).__name__}"
                log("Gemini:", last)
                busy = True
                continue
            if r.status_code == 200:
                try:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
                except (KeyError, IndexError):
                    last = f"{model}: пустой ответ"
                    continue
            last = f"{model}: {r.status_code} {r.text[:200]}"
            log("Gemini:", last.replace("\n", " "))
            if r.status_code in (400, 403, 404, 429):
                _dead.add(model)  # модель недоступна/лимит исчерпан — в этом запуске больше не пробуем
            if r.status_code in (429, 500, 502, 503, 504):
                busy = True
            time.sleep(4)
        if not _gemini_models(key):
            break
        time.sleep(60 * (rnd + 1))
    if busy:
        raise LLMBusy(f"Gemini перегружен: {last}")
    raise RuntimeError(f"Gemini не ответил: {last}")


def _claude(system: str, user: str) -> str:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={
            "model": env("CLAUDE_MODEL", "claude-haiku-5-5"),
            "max_tokens": 6000,
            "system": system + "\nОтвечай ТОЛЬКО валидным JSON без пояснений.",
            "messages": [{"role": "user", "content": user}],
        },
        timeout=180,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])


def ask_json(system: str, user: str) -> dict:
    provider = "claude" if env("ANTHROPIC_API_KEY") else "gemini"
    if provider == "gemini" and not env("GEMINI_API_KEY"):
        raise RuntimeError("Нет ключа ИИ: задайте секрет GEMINI_API_KEY (бесплатно) или ANTHROPIC_API_KEY")
    fn = _claude if provider == "claude" else _gemini
    for attempt in range(2):
        try:
            return _parse_json(fn(system, user))
        except (json.JSONDecodeError, KeyError) as e:
            log(f"ИИ вернул некорректный JSON ({e}), повтор…")
    return _parse_json(fn(system, user))
