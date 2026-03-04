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
    hook = _base_hook(source_text)
    tags = " ".join(dedupe_keep_order([tag.strip() for tag in hashtags if tag.strip()]))

    templates = [
        "{hook}",
        "No te lo pierdas: {hook}",
        "Mira esto: {hook}",
        "Top clip de hoy: {hook}",
        "Esto se hizo viral: {hook}",
    ]

    out: List[str] = []
    for template in templates:
        title = template.format(hook=hook).strip()
        if tags:
            title = f"{title} {tags}".strip()
        out.append(truncate_text(title, max_length))
        if len(out) >= suggestions_count:
            break
    return out


def write_titles_csv(rows: List[Dict[str, str]], output_csv: Path, max_suggestions: int) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    suggestion_fields = [f"suggested_title_{i + 1}" for i in range(max_suggestions)]
    fields = ["source_url", "tweet_id", "output_file", "overlay_text", *suggestion_fields]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
