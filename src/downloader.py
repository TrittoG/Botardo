from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .utils import require_success, run_command


@dataclass
class DownloadedVideo:
    source_url: str
    tweet_id: str
    title: str
    uploader: str
    downloaded_path: Path


def _extract_metadata(yt_dlp_bin: str, url: str) -> Dict[str, str]:
    cmd = [yt_dlp_bin, "--no-playlist", "--dump-single-json", url]
    result = run_command(cmd)
    require_success(result, cmd)
    raw = json.loads(result.stdout)
    return {
        "id": str(raw.get("id") or ""),
        "title": str(raw.get("title") or ""),
        "uploader": str(raw.get("uploader") or raw.get("channel") or ""),
    }


def _find_downloaded_file(downloads_dir: Path, stem: str) -> Optional[Path]:
    for candidate in downloads_dir.glob(f"{stem}.*"):
        if candidate.suffix in {".part", ".json"}:
            continue
        if candidate.name.endswith(".info.json"):
            continue
        if candidate.is_file():
            return candidate
    return None


def download_tweet_video(yt_dlp_bin: str, url: str, downloads_dir: Path) -> DownloadedVideo:
    downloads_dir.mkdir(parents=True, exist_ok=True)
    metadata = _extract_metadata(yt_dlp_bin, url)
    tweet_id = metadata["id"] or f"video_{abs(hash(url))}"
    output_tpl = str(downloads_dir / f"{tweet_id}.%(ext)s")

    cmd = [
        yt_dlp_bin,
        "--no-playlist",
        "--restrict-filenames",
        "--merge-output-format",
        "mp4",
        "-f",
        "bv*+ba/b",
        "-o",
        output_tpl,
        url,
    ]
    result = run_command(cmd)
    require_success(result, cmd)

    downloaded = _find_downloaded_file(downloads_dir, tweet_id)
    if downloaded is None:
        raise FileNotFoundError(f"No se encontro el archivo descargado para {tweet_id}.")

    return DownloadedVideo(
        source_url=url,
        tweet_id=tweet_id,
        title=metadata["title"],
        uploader=metadata["uploader"],
        downloaded_path=downloaded,
    )
