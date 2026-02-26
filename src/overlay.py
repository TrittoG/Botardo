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


def build_overlay_text(raw_text: str, max_chars: int, wrap_width: int) -> str:
    base = clean_text(raw_text)
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

    font_file = str(overlay_cfg.get("font_file", "") or "").strip()
    font_arg = f":fontfile={font_file}" if font_file else ""
    box_enabled = bool(overlay_cfg.get("box", True))
    box_flag = "1" if box_enabled else "0"

    drawtext = (
        f"drawtext=text='{escaped}'{font_arg}"
        f":x={overlay_cfg.get('x_expr', '(w-text_w)/2')}"
        f":y={overlay_cfg.get('y_expr', 'h*0.08')}"
        f":fontsize={overlay_cfg.get('font_size', 58)}"
        f":fontcolor={overlay_cfg.get('font_color', 'white')}"
        f":box={box_flag}"
        f":boxcolor={overlay_cfg.get('box_color', 'black@0.45')}"
        f":boxborderw={overlay_cfg.get('box_border', 16)}"
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
