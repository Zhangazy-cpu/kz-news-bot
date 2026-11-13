"""Обращение к ИИ: бесплатный Gemini (по умолчанию) или Claude (если задан ключ)."""
import json
import re
import time

import requests

from . import env, log

GEMINI_MODELS = [m for m in [env("GEMINI_MODEL"), "gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest"] if m]


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


def _gemini(system: str, user: str) -> str:
    key = env("GEMINI_API_KEY")
    last = None
    for model in GEMINI_MODELS:
        for attempt in range(3):
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.55},
                },
                timeout=120,
            )
            if r.status_code == 200:
                parts = r.json()["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts)
            last = f"{model}: {r.status_code} {r.text[:300]}"
            log("Gemini:", last)
            if r.status_code in (429, 500, 503):
                time.sleep(20 * (attempt + 1))
                continue
            break  # 404 и т.п. — пробуем следующую модель
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
