# music__player

Final desktop music player based on the attached architecture.

## Features

- Tkinter GUI
- `tkinter.filedialog` folder picker
- `pygame.mixer` playback engine
- `os`-based folder loading
- Play, Pause, Stop, Next, Previous
- Volume slider
- Elapsed time label
- Total duration label
- Progress bar
- Song list loaded from a local folder
- Bundled `songs` folder loaded on startup when available
- MP3 support, plus WAV and OGG where `pygame.mixer` supports them

## Install

```powershell
cd C:\Users\david\Documents\Codex\2026-08-11\bas\outputs\music__player
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The project uses `pygame-ce` because it provides the `pygame` module, including `pygame.mixer`, with current Windows wheels for newer Python versions such as Python 3.14. If classic `pygame` was installed first and conflicts, run:

```powershell
python -m pip uninstall -y pygame
python -m pip install -r requirements.txt
```

## Run

```powershell
python music_player.py
```

Or after editable install:

```powershell
python -m pip install -e .
music__player
```

## How To Use

1. Click `Load Folder`.
2. Select a folder containing MP3 files.
3. Choose a song from the list.
4. Use Play, Pause, Stop, Previous, Next, and Volume.

The project also includes an imported `songs` folder with 68 audio files from:

```text
E:\BackUp\DAGV\music
```

Click `Load Project Songs` to reload those bundled tracks at any time. The app scans subfolders recursively, so files inside folders such as `Media Sync` are included.

## Architecture

```text
music_player.py

Tkinter GUI
  - song list
  - current song
  - elapsed time
  - total duration
  - volume
  - play / pause / stop / previous / next

pygame.mixer
  - local MP3 files
```

The project is intentionally simple and scalable: UI state is kept inside `MusicPlayerApp`, folder scanning is isolated in `find_audio_files`, and playback responsibilities are routed through `pygame.mixer`.
