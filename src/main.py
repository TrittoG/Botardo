from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Set

from .config import ensure_parent_dir, load_settings, resolve_path
from .downloader import download_tweet_video
from .overlay import apply_text_overlay, build_overlay_text
from .reframe import reframe_to_vertical
from .titles import generate_title_suggestions, write_titles_csv
from .utils import load_json_file, read_urls, write_json_file


def _load_processed(state_file: Path) -> Set[str]:
    data = load_json_file(state_file, default={"processed_urls": []})
    urls = data.get("processed_urls", [])
    if not isinstance(urls, list):
        return set()
    return set(str(x) for x in urls)


def _save_processed(state_file: Path, urls: Set[str]) -> None:
    write_json_file(state_file, {"processed_urls": sorted(urls)})


def _must_get(section: Dict[str, object], key: str) -> object:
    if key not in section:
        raise KeyError(f"Falta clave requerida: {key}")
    return section[key]


def run_pipeline(config_path: str) -> None:
    project_root = Path.cwd()
    settings = load_settings(config_path)

    tools = settings.get("tools", {})
    paths = settings.get("paths", {})
    video_cfg = settings.get("video", {})
    overlay_cfg = settings.get("overlay", {})
    titles_cfg = settings.get("titles", {})
    processing_cfg = settings.get("processing", {})

    yt_dlp_bin = str(_must_get(tools, "yt_dlp_bin"))
    ffmpeg_bin = str(_must_get(tools, "ffmpeg_bin"))
    if shutil.which(yt_dlp_bin) is None:
        raise FileNotFoundError(
            f"No se encontro '{yt_dlp_bin}' en PATH. "
            "En Windows puedes instalarlo con winget/choco o indicar ruta completa en config/settings.yaml."
        )
    if shutil.which(ffmpeg_bin) is None:
        raise FileNotFoundError(
            f"No se encontro '{ffmpeg_bin}' en PATH. "
            "En Windows puedes instalarlo con winget/choco o indicar ruta completa en config/settings.yaml."
        )

    urls_file = resolve_path(str(_must_get(paths, "urls_file")), project_root)
    downloads_dir = resolve_path(str(_must_get(paths, "downloads_dir")), project_root)
    processed_dir = resolve_path(str(_must_get(paths, "processed_dir")), project_root)
    ready_dir = resolve_path(str(_must_get(paths, "ready_dir")), project_root)
    metadata_csv = resolve_path(str(_must_get(paths, "metadata_csv")), project_root)
    state_file = resolve_path(str(_must_get(paths, "state_file")), project_root)

    ensure_parent_dir(metadata_csv)
    ensure_parent_dir(state_file)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    ready_dir.mkdir(parents=True, exist_ok=True)

    urls = read_urls(urls_file)
    if not urls:
        print(f"No hay URLs para procesar en: {urls_file}")
        return

    skip_if_processed = bool(processing_cfg.get("skip_if_processed", True))
    processed_urls = _load_processed(state_file)

    width = int(video_cfg.get("target_width", 1080))
    height = int(video_cfg.get("target_height", 1920))
    reframe_mode = str(video_cfg.get("reframe_mode", "crop_center"))
    crf = int(video_cfg.get("crf", 22))
    preset = str(video_cfg.get("preset", "medium"))
    audio_bitrate = str(video_cfg.get("audio_bitrate", "128k"))

    overlay_enabled = bool(overlay_cfg.get("enabled", True))
    max_chars = int(overlay_cfg.get("max_chars", 90))
    wrap_width = int(overlay_cfg.get("wrap_width", 24))

    suggestions_count = int(titles_cfg.get("suggestions_count", 3))
    max_length = int(titles_cfg.get("max_length", 95))
    hashtags = list(titles_cfg.get("hashtags", []))

    csv_rows: List[Dict[str, str]] = []

    for url in urls:
        if skip_if_processed and url in processed_urls:
            print(f"[SKIP] URL ya procesada: {url}")
            continue

        print(f"[1/4] Descargando: {url}")
        downloaded = download_tweet_video(yt_dlp_bin, url, downloads_dir)

        vertical_path = processed_dir / f"{downloaded.tweet_id}_vertical.mp4"
        print(f"[2/4] Reencuadre 9:16: {vertical_path.name}")
        reframe_to_vertical(
            ffmpeg_bin=ffmpeg_bin,
            input_video=downloaded.downloaded_path,
            output_video=vertical_path,
            width=width,
            height=height,
            mode=reframe_mode,
            crf=crf,
            preset=preset,
            audio_bitrate=audio_bitrate,
        )

        overlay_text = build_overlay_text(downloaded.title, max_chars=max_chars, wrap_width=wrap_width)
        final_path = ready_dir / f"{downloaded.tweet_id}_short.mp4"
        if overlay_enabled and overlay_text:
            print(f"[3/4] Overlay de texto: {final_path.name}")
            apply_text_overlay(
                ffmpeg_bin=ffmpeg_bin,
                input_video=vertical_path,
                output_video=final_path,
                text=overlay_text,
                overlay_cfg=overlay_cfg,
            )
        else:
            shutil.copy2(vertical_path, final_path)

        title_base = downloaded.title or f"Clip de @{downloaded.uploader}".strip()
        suggestions = generate_title_suggestions(
            source_text=title_base,
            hashtags=hashtags,
            suggestions_count=suggestions_count,
            max_length=max_length,
        )
        print(f"[4/4] Titulos sugeridos generados: {len(suggestions)}")

        row: Dict[str, str] = {
            "source_url": downloaded.source_url,
            "tweet_id": downloaded.tweet_id,
            "output_file": str(final_path),
            "overlay_text": overlay_text,
        }
        for i in range(suggestions_count):
            row[f"suggested_title_{i + 1}"] = suggestions[i] if i < len(suggestions) else ""
        csv_rows.append(row)

        processed_urls.add(url)
        _save_processed(state_file, processed_urls)
        print(f"[OK] Video listo: {final_path}")

    if csv_rows:
        write_titles_csv(csv_rows, metadata_csv, max_suggestions=suggestions_count)
        print(f"CSV generado: {metadata_csv}")
    else:
        print("No hubo nuevos videos para exportar CSV.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline local para shorts: descarga, formato 9:16, overlay y titulos."
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Ruta al archivo de configuracion YAML.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.config)
