from queue import Queue, Empty
from threading import Thread
from typing import Optional

import numpy as np
from blessed import Terminal
from pygame import mixer

from app_data import APP_DATA
from domain.music_library import MusicLibrary
from domain.song import Song
from ui import UserInterface


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


class App:

    def __init__(self, music_lib: MusicLibrary):
        self.music_lib = music_lib
        self.data = APP_DATA
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
        self.load_ui(song)
        self.play_thread = Thread(target=self.player.play, args=[song.path])
        self.ui_thread.start()
        self.play_thread.start()
        self.play_thread.join()
        self.ui_thread.join()

    def load_ui(self, song: Song):
        audio = song.audio()
        data = np.array(audio.get_array_of_samples()[0::2])
        self.ui_thread = Thread(target=self.ui.render, args=[data, audio.max_possible_amplitude, audio.frame_rate,
                                                             audio.duration_seconds])

    def start_ui(self, song: Song):
        self.load_ui(song)
        self.ui_thread.start()

    def restart_ui(self):
        song = self.data.current()[1][mixer.music.get_pos():]
        self.start_ui(song)

    def stop(self):
        if mixer.music.get_busy():
            self.player.stop()
            self.ui.terminate()

    def pause(self):
        if mixer.music.get_busy():
            self.player.pause()
            self.ui.terminate()

    def restart(self):
        self.restart_ui()
        self.player.unpause()

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
                    elif key == 'q':
                        self.ui.terminate()
                        self.ui_thread.join()
                        self.ui.clear()
                        self.data.set_query_mode(True)
                    elif key.name == 'KEY_ESCAPE':
                        self.stop()
                        self.data.end()
                        return
            if self.data.get_query_mode():
                query = input()
                success = self.music_lib.download_and_play_song(query, True, True)
                if success:
                    self.data.set_query_mode(False)
                    self.stop()
                else:
                    ret = input("No song found, return to player Y/N")
                    if ret == "Y":
                        self.data.set_query_mode(False)
                        self.restart_ui()




