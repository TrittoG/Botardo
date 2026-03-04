from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Sequence

from .utils import clean_tweet_text, dedupe_keep_order, truncate_text


def _base_hook(text: str) -> str:
    """
    Limpia el texto del tweet para generar un título base.
    Usa la misma lógica de limpieza que el overlay.
    """
    value = clean_tweet_text(text)

    # Eliminar hashtags del título (opcional)
    value = re.sub(r"#\w+", "", value).strip()

    if not value:
        return "Video que vale la pena ver"

    return value


def generate_title_suggestions(
    source_text: str,
    hashtags: Sequence[str],
    suggestions_count: int,
    max_length: int,
) -> List[str]:
    """
    Genera títulos sugeridos simples basados en el texto del tweet.
    Primera sugerencia: solo el texto limpio
    Otras sugerencias: variaciones simples
    """
    hook = _base_hook(source_text)
    tags = " ".join(dedupe_keep_order([tag.strip() for tag in hashtags if tag.strip()]))

    # Título 1: Solo el texto limpio (sin hashtags)
    title_1 = truncate_text(hook, max_length)

    # Título 2: Texto con hashtags
    title_2 = f"{hook} {tags}".strip() if tags else hook
    title_2 = truncate_text(title_2, max_length)

    # Título 3: Variación corta con un prefijo simple (solo si es diferente)
    title_3 = f"Mirá: {hook}".strip()
    title_3 = truncate_text(title_3, max_length)

    # Eliminar duplicados manteniendo el orden
    out = dedupe_keep_order([title_1, title_2, title_3])

    # Retornar solo la cantidad solicitada
    return out[:suggestions_count]


def write_titles_csv(rows: List[Dict[str, str]], output_csv: Path, max_suggestions: int) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    suggestion_fields = [f"suggested_title_{i + 1}" for i in range(max_suggestions)]
    fields = ["source_url", "tweet_id", "output_file", "overlay_text", *suggestion_fields]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
