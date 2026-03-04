from __future__ import annotations

from pathlib import Path

from .utils import require_success, run_command


def _crop_filter(width: int, height: int, crop_scale: float = 1.0, crop_position: float = 0.5) -> str:
    """
    Crea un filtro de crop con zoom y posición horizontal controlables.

    Args:
        width: Ancho objetivo (ej: 1080)
        height: Alto objetivo (ej: 1920)
        crop_scale: Factor de zoom (0.5-1.0).
                   1.0 = crop completo (comportamiento original, sin barras negras)
                   < 1.0 = menos zoom, muestra más contenido lateral con barras negras arriba/abajo
        crop_position: Posición horizontal del crop (0.0-1.0).
                      0.0 = enfoca el lado izquierdo
                      0.5 = enfoca el centro (comportamiento original)
                      1.0 = enfoca el lado derecho

    Ejemplos con video 1920x1080 horizontal a 1080x1920 vertical:
        crop_scale=1.0: Escala a 3413x1920, crop a 1080x1920 (pierde contenido lateral)
        crop_scale=0.8: Escala a 2730x1536, crop a 1080x1536, pad a 1080x1920 (barras negras 192px arriba/abajo)
        crop_scale=0.6: Escala a 2048x1152, crop a 1080x1152, pad a 1080x1920 (barras negras 384px arriba/abajo)
    """
    if crop_scale >= 0.99:  # Comportamiento original: crop completo sin barras negras
        # Calcular posición X del crop
        # (iw - ow) es el espacio disponible para mover el crop horizontalmente
        # crop_position determina qué porcentaje de ese espacio usar
        x_pos = f"(iw-{width})*{crop_position}"

        return (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}:{x_pos}:(ih-{height})/2"
        )
    else:
        # Calcular altura escalada según crop_scale
        # Esto controla cuánto del frame vertical queremos llenar
        scaled_height = int(height * crop_scale)

        # Calcular posición X del crop
        x_pos = f"(iw-{width})*{crop_position}"

        return (
            f"scale={width}:{scaled_height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{scaled_height}:{x_pos}:(ih-{scaled_height})/2,"
            f"pad={width}:{height}:0:(oh-ih)/2:black"
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
    crop_scale: float,
    crop_position: float,
    crf: int,
    preset: str,
    audio_bitrate: str,
) -> None:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    vf = _blur_filter(width, height) if mode == "blur_background" else _crop_filter(width, height, crop_scale, crop_position)

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
