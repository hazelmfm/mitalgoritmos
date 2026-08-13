from __future__ import annotations

import os
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import pygame
except ImportError:  # pragma: no cover - handled at runtime for clear UX
    pygame = None


AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SONGS_FOLDER = PROJECT_ROOT / "songs"


@dataclass(frozen=True, slots=True)
class SongTrack:
    """Represents one audio file loaded from disk."""

    path: Path

    @property
    def title(self) -> str:
        return self.path.stem


def format_time(seconds: float | int | None) -> str:
    """Format seconds as mm:ss for elapsed and total duration labels."""

    if seconds is None or seconds < 0:
        seconds = 0
    total_seconds = int(seconds)
    minutes, remaining = divmod(total_seconds, 60)
    return f"{minutes:02d}:{remaining:02d}"


def find_audio_files(folder: str | Path) -> list[SongTrack]:
    """Load songs from a folder using os, as required by the architecture."""

    folder_path = Path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    tracks: list[SongTrack] = []
    for root, _directories, file_names in os.walk(folder_path):
        root_path = Path(root)
        for file_name in file_names:
            path = root_path / file_name
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                tracks.append(SongTrack(path=path))

    return sorted(tracks, key=lambda song: song.title.casefold())


class MusicPlayerApp:
    """Tkinter GUI that controls MP3 playback through pygame.mixer."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("music__player")
        self.root.geometry("900x560")
        self.root.minsize(760, 500)

        self.songs: list[SongTrack] = []
        self.current_index = -1
        self.current_duration = 0.0
        self.is_paused = False
        self.is_playing = False
        self.started_at = 0.0
        self.paused_at = 0.0
        self.total_paused_time = 0.0

        self._configure_style()
        self._build_layout()
        self._initialize_mixer()
        self.load_project_songs(show_empty=False)
        self._schedule_time_update()

    def load_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select a folder with MP3 files")
        if not folder:
            return

        self._load_songs_from_folder(Path(folder), show_empty=True)

    def load_project_songs(self, show_empty: bool = True) -> None:
        self._load_songs_from_folder(DEFAULT_SONGS_FOLDER, show_empty=show_empty)

    def _load_songs_from_folder(self, folder: Path, show_empty: bool) -> None:
        self.songs = find_audio_files(folder)
        self.current_index = 0 if self.songs else -1
        self.song_list.delete(0, tk.END)
        for song in self.songs:
            try:
                label = str(song.path.relative_to(folder))
            except ValueError:
                label = song.title
            self.song_list.insert(tk.END, label)

        self.folder_label.configure(text=str(folder))
        self.total_label.configure(text="00:00")
        self.elapsed_label.configure(text="00:00")
        self.progress.configure(value=0, maximum=1)
        self.current_song_label.configure(
            text=self.songs[self.current_index].title if self.songs else "No songs loaded"
        )

        if show_empty and not self.songs:
            messagebox.showinfo("music__player", "No MP3, WAV, or OGG files were found in this folder.")

    def play(self) -> None:
        if not self._mixer_ready():
            return
        if not self.songs:
            messagebox.showinfo("music__player", "Load a folder with MP3 files first.")
            return

        selected = self.song_list.curselection()
        if selected and selected[0] != self.current_index:
            self.current_index = selected[0]
            self._start_current_song()
            return

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.total_paused_time += time.monotonic() - self.paused_at
            self.is_paused = False
            self.is_playing = True
            self.status_label.configure(text="Playing")
            return

        if not self.is_playing:
            if self.current_index < 0:
                self.current_index = 0
            self._start_current_song()

    def pause(self) -> None:
        if not self._mixer_ready() or not self.is_playing or self.is_paused:
            return
        pygame.mixer.music.pause()
        self.paused_at = time.monotonic()
        self.is_paused = True
        self.status_label.configure(text="Paused")

    def stop(self) -> None:
        if not self._mixer_ready():
            return
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.started_at = 0.0
        self.paused_at = 0.0
        self.total_paused_time = 0.0
        self.elapsed_label.configure(text="00:00")
        self.progress.configure(value=0)
        self.status_label.configure(text="Stopped")

    def next_song(self) -> None:
        if not self.songs:
            return
        self.current_index = (self.current_index + 1) % len(self.songs)
        self._start_current_song()

    def previous_song(self) -> None:
        if not self.songs:
            return
        self.current_index = (self.current_index - 1) % len(self.songs)
        self._start_current_song()

    def set_volume(self, value: str) -> None:
        volume = float(value) / 100
        self.volume_value.configure(text=f"{int(float(value)):>3}%")
        if self._mixer_ready(show_error=False):
            pygame.mixer.music.set_volume(volume)

    def _start_current_song(self) -> None:
        if not self._mixer_ready():
            return
        if self.current_index < 0 or self.current_index >= len(self.songs):
            return

        song = self.songs[self.current_index]
        try:
            pygame.mixer.music.load(str(song.path))
            pygame.mixer.music.set_volume(self.volume_slider.get() / 100)
            pygame.mixer.music.play()
            self.current_duration = self._read_duration(song)
            self.started_at = time.monotonic()
            self.paused_at = 0.0
            self.total_paused_time = 0.0
            self.is_paused = False
            self.is_playing = True
            self.current_song_label.configure(text=song.title)
            self.total_label.configure(text=format_time(self.current_duration))
            self.status_label.configure(text="Playing")
            self.song_list.selection_clear(0, tk.END)
            self.song_list.selection_set(self.current_index)
            self.song_list.activate(self.current_index)
            self.song_list.see(self.current_index)
        except Exception as exc:
            messagebox.showerror("Playback error", f"Could not play this file:\n{song.path}\n\n{exc}")
            self.stop()

    def _read_duration(self, song: SongTrack) -> float:
        try:
            sound = pygame.mixer.Sound(str(song.path))
            return float(sound.get_length())
        except Exception:
            return 0.0

    def _elapsed_seconds(self) -> float:
        if not self.is_playing or self.started_at == 0:
            return 0.0
        if self.is_paused:
            return max(0.0, self.paused_at - self.started_at - self.total_paused_time)
        return max(0.0, time.monotonic() - self.started_at - self.total_paused_time)

    def _schedule_time_update(self) -> None:
        elapsed = self._elapsed_seconds()
        self.elapsed_label.configure(text=format_time(elapsed))

        if self.current_duration > 0:
            self.progress.configure(maximum=self.current_duration, value=min(elapsed, self.current_duration))

        if self.is_playing and not self.is_paused and self.current_duration > 0:
            if elapsed >= self.current_duration - 0.25:
                self.next_song()

        self.root.after(500, self._schedule_time_update)

    def _initialize_mixer(self) -> None:
        if pygame is None:
            self.status_label.configure(text="pygame is not installed")
            messagebox.showerror(
                "Missing dependency",
                "pygame-ce is required for playback.\n\nInstall it with:\npython -m pip install -r requirements.txt",
            )
            return

        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume_slider.get() / 100)
            self.status_label.configure(text="Ready")
        except Exception as exc:
            self.status_label.configure(text="Audio unavailable")
            messagebox.showerror("Audio error", f"pygame.mixer could not start:\n{exc}")

    def _mixer_ready(self, show_error: bool = True) -> bool:
        ready = pygame is not None and pygame.mixer.get_init() is not None
        if not ready and show_error:
            messagebox.showerror(
                "Audio unavailable",
                "pygame.mixer is not ready. Check that pygame is installed and an audio device is available.",
            )
        return ready

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.root, padding=18)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.columnconfigure(1, weight=2)
        shell.rowconfigure(1, weight=1)

        title = ttk.Label(shell, text="music__player", style="Title.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        left = ttk.Frame(shell, style="Panel.TFrame", padding=14)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        folder_buttons = ttk.Frame(left)
        folder_buttons.grid(row=0, column=0, sticky="ew")
        folder_buttons.columnconfigure(0, weight=1)
        folder_buttons.columnconfigure(1, weight=1)
        ttk.Button(folder_buttons, text="Load Project Songs", command=self.load_project_songs).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(folder_buttons, text="Load Folder", command=self.load_folder).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        self.folder_label = ttk.Label(left, text="No folder selected", style="Muted.TLabel", wraplength=260)
        self.folder_label.grid(row=1, column=0, sticky="ew", pady=(10, 10))

        list_frame = ttk.Frame(left)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.song_list = tk.Listbox(
            list_frame,
            activestyle="none",
            bg="#161616",
            fg="#f8fafc",
            selectbackground="#1db954",
            selectforeground="#061008",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#303030",
        )
        self.song_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.song_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.song_list.configure(yscrollcommand=scrollbar.set)
        self.song_list.bind("<Double-Button-1>", lambda _event: self.play())

        right = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Current song", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.current_song_label = ttk.Label(right, text="No songs loaded", style="Song.TLabel", wraplength=460)
        self.current_song_label.grid(row=1, column=0, sticky="ew", pady=(4, 18))

        time_row = ttk.Frame(right)
        time_row.grid(row=2, column=0, sticky="ew")
        time_row.columnconfigure(1, weight=1)
        self.elapsed_label = ttk.Label(time_row, text="00:00", width=7)
        self.elapsed_label.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(time_row, orient=tk.HORIZONTAL, mode="determinate", maximum=1)
        self.progress.grid(row=0, column=1, sticky="ew", padx=10)
        self.total_label = ttk.Label(time_row, text="00:00", width=7)
        self.total_label.grid(row=0, column=2, sticky="e")

        controls = ttk.Frame(right)
        controls.grid(row=3, column=0, sticky="ew", pady=(24, 18))
        for index in range(5):
            controls.columnconfigure(index, weight=1)

        ttk.Button(controls, text="Previous", command=self.previous_song).grid(row=0, column=0, sticky="ew", padx=4)
        ttk.Button(controls, text="Play", command=self.play).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(controls, text="Pause", command=self.pause).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(controls, text="Stop", command=self.stop).grid(row=0, column=3, sticky="ew", padx=4)
        ttk.Button(controls, text="Next", command=self.next_song).grid(row=0, column=4, sticky="ew", padx=4)

        volume = ttk.Frame(right)
        volume.grid(row=4, column=0, sticky="ew")
        volume.columnconfigure(1, weight=1)
        ttk.Label(volume, text="Volume").grid(row=0, column=0, sticky="w")
        self.volume_slider = ttk.Scale(volume, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_slider.set(70)
        self.volume_slider.grid(row=0, column=1, sticky="ew", padx=12)
        self.volume_value = ttk.Label(volume, text=" 70%", width=5)
        self.volume_value.grid(row=0, column=2, sticky="e")

        self.status_label = ttk.Label(right, text="Starting...", style="Muted.TLabel")
        self.status_label.grid(row=5, column=0, sticky="w", pady=(24, 0))

    def _configure_style(self) -> None:
        self.root.configure(bg="#101010")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#101010", foreground="#f8fafc", font=("Segoe UI", 10))
        style.configure("Panel.TFrame", background="#181818", relief="flat")
        style.configure("Title.TLabel", background="#101010", foreground="#1db954", font=("Segoe UI", 24, "bold"))
        style.configure("Song.TLabel", background="#181818", foreground="#f8fafc", font=("Segoe UI", 18, "bold"))
        style.configure("Muted.TLabel", background="#181818", foreground="#a1a1aa")
        style.configure("TButton", background="#242424", foreground="#f8fafc", borderwidth=0, focusthickness=0, padding=10)
        style.map("TButton", background=[("active", "#1db954")], foreground=[("active", "#071108")])
        style.configure("Horizontal.TProgressbar", background="#1db954", troughcolor="#2a2a2a", bordercolor="#2a2a2a")
        style.configure("Horizontal.TScale", background="#181818", troughcolor="#2a2a2a")


def main() -> None:
    root = tk.Tk()
    MusicPlayerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
