import time
import traceback
from threading import Thread
from typing import Optional

from blessed import Terminal
from pygame import mixer

from term_music.app_data import APP_DATA
from term_music.config import KEYMAP, UI_SETTINGS
from term_music.domain.music_library import MusicLibrary
from term_music.domain.song import Song
from term_music.keyboard import Keyboard
from term_music.player import Player
from term_music.ui import UserInterface


class App:

    def __init__(self, data: APP_DATA, music_lib: MusicLibrary, config):
        self.music_lib = music_lib
        self.data = data
        self.player = Player(data)
        self.terminal = Terminal()
        self.ui = UserInterface(data, self.terminal, **config.ui_settings)
        self.ui_thread: Optional[Thread] = None
        self.play_thread: Optional[Thread] = None
        self.keyboard_thread: Optional[Thread] = None
        self.keyboard = Keyboard(data, self.terminal,
                                 {key: getattr(self, value) for key, value in config.keymap.items()})

    def play(self, path):
        self.data.add_song(path)

    def play_audio(self, song: Song):
        self.play_thread = Thread(target=self.player.play, args=[song.path])
        self.start_ui(song)
        self.play_thread.start()

    def load_ui(self, song: Song):
        audio = song.audio()
        frames = self.ui.get_frames(audio)
        self.ui_thread = Thread(target=self.ui.render, args=[frames, audio.duration_seconds])

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

    def wait_keyboard(self):
        if self.keyboard.is_blocking:
            print("press any key to continue")
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

    def get_no_songs_prompt(self):
        prompts = ["No songs to play", "p - play all songs in music library", "q - enter query mode"]
        if self.data.length() > 0:
            prompts.append("r - restart with current history")
        prompts.append("press any key to exit: ")
        return "\n".join(prompts)

    def run(self):
        try:
            if self.data.has_songs():
                self.start_keyboard()
            while self.data.running():
                if self.data.is_query_mode():
                    query = input("Search: \n")
                    success = self.music_lib.download_and_play_song(query, True, True)
                    if success:
                        if self.is_playing():
                            self.stop()
                        self.data.normal_mode()
                        self.restart_keyboard()
                    else:
                        return_mode = "return to player" if self.data.has_songs() else "exit"
                        ret = input(f"No song found, {return_mode} Y/N: ")
                        if ret == "Y":
                            if return_mode == "return to player":
                                self.data.normal_mode()
                                self.restart_keyboard()
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
                    self.wait_ui()
                    self.wait_keyboard()
                    self.data.reset_current()
                    mode = input(self.get_no_songs_prompt())
                    if mode == "p":
                        self.music_lib.play_all()
                        self.start_keyboard()
                    elif mode == "q":
                        self.data.query_mode()
                    elif mode == "r":
                        self.data.restart_current()
                        self.start_keyboard()
                    else:
                        self.data.end()
        except BaseException:
            self.stop()
            self.data.end()
            traceback.print_exc()
        finally:
            self.wait_player()
            self.wait_ui()
            print(self.terminal.clear)
            print(self.terminal.home)
            print(self.terminal.normal_cursor)
            self.wait_keyboard()
            print(self.terminal.normal_cursor)
            print("Exiting...")

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
