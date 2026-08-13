from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from music_player import find_audio_files, format_time


class MusicPlayerHelperTests(unittest.TestCase):
    def test_format_time(self) -> None:
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(65), "01:05")
        self.assertEqual(format_time(3601), "60:01")

    def test_find_audio_files_returns_supported_files_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "b_song.mp3").write_bytes(b"")
            nested = root / "nested"
            nested.mkdir()
            (nested / "c_song.wav").write_bytes(b"")
            (root / "a_song.ogg").write_bytes(b"")
            (root / "notes.txt").write_text("ignore", encoding="utf-8")

            songs = find_audio_files(root)

        self.assertEqual([song.title for song in songs], ["a_song", "b_song", "c_song"])


if __name__ == "__main__":
    unittest.main()
