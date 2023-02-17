import os
from queue import Queue, Empty
from threading import Thread, Lock
from typing import Optional

import numpy as np
from blessed import Terminal
from pydub import AudioSegment
from pygame import mixer

from ui import UserInterface


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


class Player:
    STOP = 'STOP'
    PAUSE = 'PAUSE'
    UNPAUSE = 'UNPAUSE'

    def __init__(self):
        mixer.init()
        self.play_queue = Queue()
        self.paused = False

    def put(self, command):
        self.play_queue.put(command)

    def stop(self):
        self.play_queue.put(self.STOP)

    def pause(self):
        self.play_queue.put(self.PAUSE)

    def unpause(self):
        self.play_queue.put(self.UNPAUSE)

    def is_paused(self):
        return self.paused

    def play(self, path):
        mixer.music.load(path)
        mixer.music.play()
        self.paused = False
        while True:
            try:
                command = self.play_queue.get_nowait()
                if command == self.STOP:
                    mixer.music.stop()
                    mixer.music.unload()
                    return
                elif command == self.PAUSE:
                    mixer.music.pause()
                    self.paused = True
                elif command == self.UNPAUSE:
                    mixer.music.unpause()
                    self.paused = False
            except Empty:
                if not mixer.music.get_busy() and not self.paused:
                    mixer.music.stop()
                    mixer.music.unload()
                    return


class Data:

    def __init__(self):
        self._current = -1
        self._selected = 0
        self._song_history = []
        self.selected_lock = Lock()
        self.current_lock = Lock()

    def length(self):
        return len(self._song_history)

    def add_song(self, song):
        self._song_history.append(song)

    def get_current(self):
        return self._current

    def end(self):
        self.set_current(self.length())

    def inc_current(self):
        self.current_lock.acquire()
        if self._current >= self.length() - 1:
            return False
        self._current += 1
        self.current_lock.release()
        return True

    def set_current(self, index):
        self.current_lock.acquire()
        self._current = index
        self.current_lock.release()

    def inc_selected(self, inc=1):
        self.selected_lock.acquire()
        new_selected = self._selected + inc
        if -1 < new_selected < len(self._song_history):
            self._selected = new_selected
        self.selected_lock.release()

    def set_selected(self, selected):
        self.selected_lock.acquire()
        if -1 < self._selected < len(self._song_history):
            self._selected = selected
        self.selected_lock.release()

    def get_selected(self):
        return self._selected

    def get_song(self, index):
        return Song(self._song_history[index])

    def previous(self):
        return self._current - 1, Song(self._song_history[self._current - 1])

    def current(self):
        return self._current, Song(self._song_history[self._current])

    def path_at(self, index):
        return self._song_history[index]


class App:

    def __init__(self):
        self.data = Data()
        self.player = Player()
        self.terminal = Terminal()
        self.ui = UserInterface(self.data, self.terminal)
        self.ui_thread: Optional[Thread] = None
        self.play_thread: Optional[Thread] = None
        self.thread = Thread(target=self.consumer, daemon=True, name="CONSUMER")
        self.keyboard_thread = Thread(target=self.keyboard, daemon=True)
        self.keyboard_thread.start()

    def play(self, path):
        self.data.add_song(path)

    def play_audio(self, song: Song):
        self.start_ui(song)
        self.play_thread = Thread(target=self.player.play, args=[song.path])
        self.play_thread.start()
        self.play_thread.join()
        self.ui_thread.join()

    def start_ui(self, song: Song):
        audio = song.audio()
        data = np.array(audio.get_array_of_samples()[0::2])
        self.ui_thread = Thread(target=self.ui.render, args=[data, audio.max_possible_amplitude, audio.frame_rate,
                                                             audio.duration_seconds])
        self.ui_thread.start()

    def stop(self):
        if mixer.music.get_busy():
            self.player.stop()
            self.ui.terminate()

    def pause(self):
        if mixer.music.get_busy():
            self.player.pause()
            self.ui.terminate()

    def restart(self):
        song = self.data.current()[1][mixer.music.get_pos():]
        self.player.unpause()
        self.start_ui(song)

    def start(self):
        self.thread.start()

    def consumer(self):
        while self.data.inc_current():
            index, song = self.data.current()
            self.data.set_selected(index)
            self.play_audio(song)

    def join(self):
        self.thread.join()
        self.keyboard_thread.join()
        print(self.terminal.clear)
        print(self.terminal.home)
        print(self.terminal.normal_cursor)

    def keyboard(self):
        while True:
            with self.terminal.cbreak():
                key = self.terminal.inkey()
                if key:
                    if key.name == 'KEY_DOWN':
                        self.data.inc_selected()
                    elif key.name == 'KEY_UP':
                        self.data.inc_selected(-1)
                    elif key == ' ':
                        if self.player.is_paused():
                            self.restart()
                        else:
                            self.pause()
                    elif key.name == 'KEY_RIGHT':
                        self.stop()
                    elif key.name == 'KEY_LEFT':
                        self.stop()
                        self.data.set_current(self.data.get_current() - 2)
                    elif key.name == 'KEY_ENTER':
                        self.stop()
                        # decreasing by 1 because consumer thread will increase by 1
                        self.data.set_current(self.data.get_selected() - 1)
                    elif key.name == 'KEY_ESCAPE':
                        self.stop()
                        self.data.end()
                        return


