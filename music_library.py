import difflib
import os
from queue import Queue, PriorityQueue, Empty
from threading import Thread, Lock
from typing import Optional

import numpy as np
import youtube_dl
from blessed import Terminal
from pydub import AudioSegment
from pygame import mixer

from ui import UserInterface


class Playlist:
    """
    Class that represents a playlist.
    Playlist is a text file saved in music lib folder.
    Each line of the file is a song title.
    Songs are saved in files with the same name as song title and extension .mp3
    """

    def __init__(self, download_folder, playlist_name):
        self.download_folder = download_folder
        self.playlist_name = playlist_name
        self.song_titles = []

    def add_song(self, song_title):
        # Add the given song title to the playlist
        self.song_titles.append(song_title)

    def remove_song(self, song_title):
        # Remove the given song title from the playlist
        self.song_titles.remove(song_title)

    def save(self):
        # Save the playlist to a file with the given name in the download folder
        playlist_file = open(os.path.join(self.download_folder, self.playlist_name), "w")
        for song_title in self.song_titles:
            playlist_file.write(song_title + "\n")
        playlist_file.close()

    @staticmethod
    def load(download_folder, playlist_name):
        # Load the playlist from the given file in the download folder
        playlist_file = open(os.path.join(download_folder, playlist_name), "r")
        song_titles = playlist_file.readlines()
        playlist_file.close()
        playlist = Playlist(download_folder, playlist_name)
        playlist.song_titles = [title.strip() for title in song_titles]
        return playlist

    def __str__(self):
        # Return a string representation of the playlist
        return "Playlist '{}' with {} songs:\n{}".format(
            self.playlist_name,
            len(self.song_titles),
            "\n".join(self.song_titles)
        )


def is_song(filename):
    return filename and filename.endswith(".mp3")


def is_playlist(filename):
    return filename and filename.endswith(".txt")


def remove_extension(filenames):
    return [f[:-4] for f in filenames]


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
                    elif key.name == 'KEY_ENTER':
                        self.stop()
                        # decreasing by 1 because consumer thread will increase by 1
                        self.data.set_current(self.data.get_selected() - 1)
                    elif key.name == 'KEY_ESCAPE':
                        self.stop()
                        self.data.end()


class MusicLibrary:
    def __init__(self, download_folder, player):
        self.download_folder = download_folder
        self.player = player
        if not os.path.exists(download_folder):
            os.mkdir(download_folder)

    def download_song(self, song_url):
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([song_url])

    def search_song(self, search_query):
        return difflib.get_close_matches(search_query, self.songs(), n=1, cutoff=0.0)

    def search_playlists(self, search_query):
        return difflib.get_close_matches(search_query, self.playlists(), n=1, cutoff=0.0)

    def search_and_play_playlist(self, search_query):
        self.play_playlist_filename(self.search_playlists(search_query)[0])

    def search_and_download(self, song_query, check=False):
        # Song not found in the local library, search YouTube
        ydl_opts = {
            "default_search": "ytsearch",
            "max_downloads": 1,
            "format": "bestaudio/best",
            "noplaylist": True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_query, download=False)
            song_title = info["entries"][0]["title"]
            if check and song_title in self.songs():
                # don't download if we already have one
                print(f"Skipped download of {song_title}")
                return song_title
            song_url = info["entries"][0]["webpage_url"]
            # Download the song
            self.download_song(song_url)
            return song_title

    def download_and_play_song(self, song_query):
        # Search the local music library for the song
        search_result = self.search_song(song_query)
        if search_result:
            # Found the song in the local library
            print(search_result)
            song_title = search_result[0]
        else:
            song_title = self.search_and_download(song_query)

        # Play the song
        self.play_song(song_title)

    def play_filename(self, filename):
        self.player.play(os.path.join(self.download_folder, filename))

    def play_song(self, song):
        self.play_filename(song + ".mp3")

    def play_playlist(self, playlist):
        self.play_playlist_filename(playlist + ".txt")

    def play(self, filename):
        if is_playlist(filename):
            self.play_playlist_filename(filename)
        else:
            self.play_filename(filename)

    def play_playlist_filename(self, playlist_filename):
        for song_title in Playlist.load(self.download_folder, playlist_filename).song_titles:
            self.play_song(song_title)

    def get_all_playlists(self):
        playlists = []
        for filename in os.listdir(self.download_folder):
            if is_playlist(filename):
                playlists.append(Playlist.load(self.download_folder, filename))
        return playlists

    def play_all(self):
        for filename in os.listdir(self.download_folder):
            # Play the file if it is an audio file
            if is_song(filename):
                self.play_filename(os.path.join(self.download_folder, filename))

    def play_all_playlists(self):
        for filename in os.listdir(self.download_folder):
            # Play the playlist if it is a text file
            if is_playlist(filename):
                self.play_playlist_filename(filename)

    def delete_song(self, song_title):
        # Delete the file with the given name from the download folder
        song_filename = f"{song_title}.mp3"
        os.remove(os.path.join(self.download_folder, song_filename))

    def song_files(self):
        return filter(is_song, os.listdir(self.download_folder))

    def playlist_files(self):
        return filter(is_playlist, os.listdir(self.download_folder))

    def get_or_create_playlist(self, playlist_name):
        if playlist_name in self.playlists():
            return Playlist.load(self.download_folder, playlist_name)
        else:
            playlist = Playlist(self.download_folder, playlist_name)
            playlist.save()
            return playlist

    def songs(self):
        return set(remove_extension(self.song_files()))

    def playlists(self):
        return set(remove_extension(self.playlist_files()))

    def print_songs_and_playlists(self):
        # Create a dictionary to map each song to the playlists it belongs to
        song_playlists = {}
        playlists = self.get_all_playlists()
        for song in self.songs():
            for playlist in playlists:
                if song in playlist.song_titles:
                    song_playlists.setdefault(song, []).append(playlist.playlist_name)

        # Print a table with each song and the playlists it belongs to
        print("{:15s}  {:s}".format("Song", "Playlists"))
        print("{:15s}  {:s}".format("----", "--------"))
        for song in self.songs():
            print("{:15s}  {:s}".format(song, ", ".join(song_playlists[song]) if song_playlists.get(song) else ""))
