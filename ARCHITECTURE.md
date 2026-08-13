# Architecture

This project follows the attached proposed architecture.

```text
music_player.py

┌───────────────────────────┐
│ Tkinter GUI               │
├───────────────────────────┤
│ Lista de canciones        │
│ Cancion actual            │
│ Tiempo actual             │
│ Duracion total            │
│ Volumen                   │
├───────────────────────────┤
│ Play                      │
│ Pause                     │
│ Stop                      │
│ Previous                  │
│ Next                      │
└───────────────────────────┘
             │
             ▼
       pygame.mixer
             │
             ▼
       Archivos MP3
```

## Code Map

- `SongTrack`: represents one loaded audio file.
- `find_audio_files`: scans a selected folder recursively with `os.walk`.
- `DEFAULT_SONGS_FOLDER`: points to the project-level `songs` folder imported from the user's music path.
- `format_time`: converts elapsed/duration seconds into `mm:ss`.
- `MusicPlayerApp`: owns the Tkinter GUI and all playback state.
- `pygame.mixer.music`: performs load, play, pause, unpause, stop, next, previous, and volume control.

## State

- `songs`: loaded song list.
- `current_index`: selected/current song index.
- `current_duration`: total duration for the current song.
- `started_at`, `paused_at`, `total_paused_time`: elapsed-time tracking.
- `is_playing`, `is_paused`: playback state.
