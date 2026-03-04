from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Dict

from .utils import clean_text, require_success, run_command, truncate_text


def _escape_drawtext(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace("%", "\\%")
    return escaped


def _escape_filter_value(value: str) -> str:
    escaped = value.replace("\\", "/")
    escaped = escaped.replace(":", r"\:")
    escaped = escaped.replace("'", r"\'")
    return escaped


def build_overlay_text(raw_text: str, max_chars: int, wrap_width: int) -> str:
    import re

    base = clean_text(raw_text)

    # Eliminar nombre de usuario al principio (ej: "@usuario: texto" o "NombreUsuario: texto")
    # Busca patrón de nombre/@ seguido de : al inicio
    base = re.sub(r'^[@\w\s]+:\s*', '', base)

    # Eliminar URLs
    base = re.sub(r'https?://\S+', '', base)

    # Eliminar menciones @usuario
    base = re.sub(r'@\w+', '', base)

    # Limpiar espacios múltiples
    base = re.sub(r'\s+', ' ', base).strip()

    base = truncate_text(base, max_chars)
    return textwrap.fill(base, width=wrap_width)


def apply_text_overlay(
    ffmpeg_bin: str,
    input_video: Path,
    output_video: Path,
    text: str,
    overlay_cfg: Dict[str, object],
) -> None:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    escaped = _escape_drawtext(text)

    font_file_raw = str(overlay_cfg.get("font_file", "") or "").strip()
    font_arg = ""
    if font_file_raw:
        font_file = _escape_filter_value(font_file_raw)
        font_arg = f":fontfile='{font_file}'"

    # Nuevo estilo: sin box, con border (outline) para legibilidad
    drawtext = (
        f"drawtext=text='{escaped}'{font_arg}"
        f":x={overlay_cfg.get('x_expr', '(w-text_w)/2')}"
        f":y={overlay_cfg.get('y_expr', 'h*0.06')}"
        f":fontsize={overlay_cfg.get('font_size', 72)}"
        f":fontcolor={overlay_cfg.get('font_color', 'white')}"
        f":borderw={overlay_cfg.get('border_width', 4)}"
        f":bordercolor={overlay_cfg.get('border_color', 'black')}"
    )

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(input_video),
        "-vf",
        drawtext,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "22",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(output_video),
    ]
    result = run_command(cmd)
    require_success(result, cmd)
