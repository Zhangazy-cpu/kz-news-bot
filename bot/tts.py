"""Казахская озвучка (бесплатный нейроголос Microsoft через edge-tts) + тайминги слов для субтитров."""
import asyncio
import re
import subprocess
from pathlib import Path

from . import log

PAD = 0.35  # пауза после каждой сцены, сек


def _dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


async def _speak(text: str, voice: str, rate: str, path: Path) -> list[tuple[str, float, float]]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    bounds = []
    with open(path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                bounds.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    return bounds


def _align(narration: str, bounds: list[tuple[str, float, float]]) -> list[dict]:
    """Привязываем слова озвучки к токенам текста (чтобы сохранить пунктуацию в субтитрах)."""
    tokens = narration.split()
    words, j = [], 0
    core = lambda s: re.sub(r"[^\w]", "", s.lower())  # noqa: E731
    for i, tok in enumerate(tokens):
        c = core(tok)
        if not c:
            continue
        hit = None
        for k in range(j, min(j + 4, len(bounds))):
            if core(bounds[k][0]) and (core(bounds[k][0]) in c or c in core(bounds[k][0])):
                hit = k
                break
        if hit is not None:
            words.append({"w": tok, "s": bounds[hit][1], "e": bounds[hit][2]})
            j = hit + 1
        else:  # слово не нашлось — ставим сразу после предыдущего
            s = words[-1]["e"] if words else 0.0
            words.append({"w": tok, "s": s, "e": s + 0.25})
    return words


def estimate(narration: str) -> tuple[float, list[dict]]:
    """Оценка таймингов без озвучки (для предпросмотра, если TTS недоступен)."""
    tokens = narration.split()
    t, words = 0.15, []
    for tok in tokens:
        d = 0.068 * len(tok) + 0.1
        words.append({"w": tok, "s": round(t, 3), "e": round(t + d, 3)})
        t += d
    return t + 0.1, words


def synthesize(scenes: list[dict], voice: str, rate: str, workdir: Path, allow_silent=False) -> Path | None:
    """Озвучивает все сцены; проставляет scene['duration'] и scene['words']; возвращает общий mp3."""
    workdir.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, sc in enumerate(scenes):
        text = sc["narration"].strip()
        p = workdir / f"s{i}.mp3"
        try:
            bounds = asyncio.run(_speak(text, voice, rate, p))
            d = _dur(p)
            sc["words"] = _align(text, bounds)
            sc["duration"] = round(d + PAD, 3)
            parts.append((p, sc["duration"]))
        except Exception as e:  # noqa: BLE001
            if not allow_silent:
                raise RuntimeError(f"Озвучка не удалась: {e}") from e
            log(f"TTS недоступен ({type(e).__name__}) — делаю предпросмотр без голоса")
            for s in scenes:
                s["duration"], s["words"] = estimate(s["narration"])
                s["duration"] = round(s["duration"] + PAD, 3)
            return None
    # склейка: каждая часть дополняется тишиной до длительности сцены
    out = workdir / "voice.mp3"
    inputs, filt = [], []
    for k, (p, d) in enumerate(parts):
        inputs += ["-i", str(p)]
        filt.append(f"[{k}:a]aresample=44100,apad=whole_dur={d}[a{k}]")
    filt.append("".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "160k", str(out)],
        check=True,
    )
    return out
