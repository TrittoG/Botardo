# Botardo - Pipeline base para shorts (gratis)

Pipeline local en Python para:

1. Leer URLs de tweets desde `input/urls.txt`
2. Descargar video con `yt-dlp`
3. Convertir a formato vertical 9:16 con `ffmpeg`
4. Agregar texto overlay
5. Exportar archivo final listo para subir
6. Generar titulos sugeridos en CSV

## Requisitos

- Python 3.10+
- `ffmpeg` instalado y disponible en PATH
- `yt-dlp` instalado y disponible en PATH

En macOS (Homebrew):

```bash
brew install ffmpeg yt-dlp
```

En Windows (PowerShell):

```powershell
winget install Gyan.FFmpeg
winget install yt-dlp.yt-dlp
```

Alternativa con Chocolatey:

```powershell
choco install ffmpeg yt-dlp -y
```

## Instalacion

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuracion

Edita `config/settings.yaml`:

- `video.reframe_mode`: `crop_center` o `blur_background`
- `overlay.*`: estilo/posicion del texto
- `titles.hashtags`: hashtags por defecto
- `tools.yt_dlp_bin` y `tools.ffmpeg_bin`: en Windows puedes dejar `yt-dlp`/`ffmpeg` o poner ruta completa al `.exe`

URLs a procesar en `input/urls.txt` (una por linea).

## Ejecucion

```bash
python -m src.main --config config/settings.yaml
```

En Windows:

```powershell
python -m src.main --config config/settings.yaml
```

## Salidas

- Descargas: `output/downloads`
- Intermedio vertical: `output/processed`
- Final listo para subir: `output/ready_to_upload`
- Titulos sugeridos: `output/metadata/titles.csv`
- Estado de URLs procesadas: `state/processed_urls.json`

## Notas

- El script evita reprocesar URLs ya tratadas (`processing.skip_if_processed: true`).
- Esta version no publica automaticamente a YouTube/TikTok.
- Si quieres cambiar fuente para overlay, define `overlay.font_file` con una ruta absoluta a `.ttf`.
- En Windows usa formato de ruta con `/` para la fuente, por ejemplo: `C:/Windows/Fonts/arial.ttf`.
