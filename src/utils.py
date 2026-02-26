from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, List, Sequence


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess[str], command: Sequence[str]) -> None:
    if result.returncode == 0:
        return
    joined = " ".join(command)
    raise RuntimeError(
        f"Fallo el comando: {joined}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def read_urls(urls_file: Path) -> List[str]:
    if not urls_file.exists():
        return []
    # utf-8-sig evita problemas con BOM generado por algunos editores en Windows.
    lines = urls_file.read_text(encoding="utf-8-sig").splitlines()
    urls: List[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def clean_text(text: str) -> str:
    value = re.sub(r"https?://\S+", "", text)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def truncate_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def dedupe_keep_order(values: Iterable[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
