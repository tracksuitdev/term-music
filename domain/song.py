import os

from pydub import AudioSegment


class Song:

    def __init__(self, path, audio=None):
        self.path = path
        self.title = os.path.basename(path)
        self._audio = audio

    def __getitem__(self, item):
        return Song(self.title, self.audio().__getitem__(item))

    def audio(self):
        if not self._audio:
            self._audio = AudioSegment.from_mp3(self.path)
        return self._audio
