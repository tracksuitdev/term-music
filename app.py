import time
from queue import Queue, Empty
from threading import Thread
from typing import Optional

import numpy as np
from blessed import Terminal
from pygame import mixer

from app_data import APP_DATA
from config import KEYMAP
from domain.music_library import MusicLibrary
from domain.song import Song
from keyboard import Keyboard
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

    def is_playing(self):
        return mixer.music.get_busy() or self.paused

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
                time.sleep(1e-6)


class App:

    def __init__(self, music_lib: MusicLibrary):
        self.music_lib = music_lib
        self.data = APP_DATA
        self.player = Player()
        self.terminal = Terminal()
        self.ui = UserInterface(self.data, self.terminal)
        self.ui_thread: Optional[Thread] = None
        self.play_thread: Optional[Thread] = None
        self.keyboard_thread: Optional[Thread] = None
        self.keyboard = Keyboard(self.terminal, {key: getattr(self, value) for key, value in KEYMAP.items()})

    def play(self, path):
        self.data.add_song(path)

    def play_audio(self, song: Song):
        self.play_thread = Thread(target=self.player.play, args=[song.path])
        self.start_ui(song)
        self.play_thread.start()

    def load_ui(self, song: Song):
        audio = song.audio()
        data = np.array(audio.get_array_of_samples()[0::2])
        self.ui_thread = Thread(target=self.ui.render, args=[data, audio.max_possible_amplitude, audio.frame_rate,
                                                             audio.duration_seconds])

    def start_ui(self, song: Song):
        self.load_ui(song)
        self.ui.unpause()
        self.ui_thread.start()

    def restart_ui(self):
        self.player.pause()
        song = self.data.current()[1][mixer.music.get_pos():]
        self.start_ui(song)
        self.player.unpause()

    def stop(self):
        self.player.stop()
        self.ui.terminate()

    def pause(self):
        if mixer.music.get_busy():
            self.player.pause()
            self.ui.pause()

    def restart(self):
        self.player.unpause()
        self.ui.unpause()

    def start_keyboard(self):
        self.keyboard_thread = Thread(target=self.keyboard.listen, daemon=True, name="KEYBOARD")
        self.keyboard_thread.start()

    def wait_till_playing(self):
        while not self.data.has_songs():
            time.sleep(1e-6)

    def wait_keyboard(self):
        if self.keyboard_thread and self.keyboard_thread.is_alive():
            self.keyboard_thread.join()

    def wait_ui(self):
        if self.ui_thread and self.ui_thread.is_alive():
            self.ui_thread.join()

    def wait_player(self):
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()

    def restart_keyboard(self):
        self.wait_keyboard()
        self.start_keyboard()
        
    def is_playing(self):
        return self.play_thread and self.play_thread.is_alive()

    def run(self):
        if self.data.has_songs():
            self.start_keyboard()
        while self.data.running():
            if self.data.is_query_mode():
                query = input("Search: \n")
                success = self.music_lib.download_and_play_song(query, True, True)
                if success:
                    if self.is_playing():
                        self.stop()
                    self.restart_keyboard()
                    self.data.normal_mode()
                else:
                    return_mode = "return to player" if self.data.has_songs() else "exit"
                    ret = input(f"No song found, {return_mode} Y/N: ")
                    if ret == "Y":
                        if return_mode == "return to player":
                            self.data.normal_mode()
                            self.restart_ui()
                        else:
                            self.data.end()
            elif self.is_playing():
                time.sleep(1e-3)
                continue
            if self.data.has_songs() and self.data.inc_current():
                index, song = self.data.current()
                self.data.set_selected(index)
                self.play_audio(song)
            else:
                self.wait_keyboard()
                self.wait_ui()
                self.data.reset_current()
                mode = input("No songs to play, p - play all songs in music library, q - enter query mode: ")
                if mode == "p":
                    self.music_lib.play_all()
                    self.start_keyboard()
                elif mode == "q":
                    self.data.query_mode()
                else:
                    self.data.end()
        self.wait_player()
        self.wait_keyboard()
        self.wait_ui()
        print(self.terminal.clear)
        print(self.terminal.home)
        print(self.terminal.normal_cursor)

    # keyboard actions ---------------------------------------------
    def action_down(self):
        self.data.inc_selected()

    def action_up(self):
        self.data.inc_selected(-1)

    def action_pause(self):
        if self.player.is_paused():
            self.restart()
        else:
            self.pause()

    def action_next(self):
        self.stop()

    def action_previous(self):
        self.stop()
        # decreasing by 2 because consumer thread will increase by 1
        self.data.set_current(self.data.get_current() - 2)

    def action_select(self):
        self.stop()
        # decreasing by 1 because consumer thread will increase by 1
        self.data.set_current(self.data.get_selected() - 1)

    def action_query_mode(self):
        self.ui.terminate()
        self.ui_thread.join()
        self.ui.clear()
        self.data.query_mode()

    def action_exit(self):
        self.stop()
        self.data.end()

    # ----------------------------------------------------------------
