from __future__ import annotations

from pathlib import Path

from .utils import require_success, run_command


def _crop_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )


def _blur_filter(width: int, height: int) -> str:
    return (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,boxblur=20:10[bg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
    )


def reframe_to_vertical(
    ffmpeg_bin: str,
    input_video: Path,
    output_video: Path,
    width: int,
    height: int,
    mode: str,
    crf: int,
    preset: str,
    audio_bitrate: str,
) -> None:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    vf = _blur_filter(width, height) if mode == "blur_background" else _crop_filter(width, height)

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(input_video),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
        str(output_video),
    ]
    result = run_command(cmd)
    require_success(result, cmd)
