import os
import time
import traceback
from multiprocessing import Process
from queue import Queue, PriorityQueue
from threading import Thread
from typing import Optional

import youtube_dl
import difflib

import numpy as np
from blessed import Terminal

from pydub import AudioSegment, playback

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


class MusicPlayer:

    def __init__(self):
        self.current = -1
        self.started_at = None
        self.paused = None
        self.queue = PriorityQueue()
        self.song_history = []
        self.terminal = Terminal()
        self.ui = UserInterface(self.terminal)
        self.ui_thread: Optional[Thread] = None
        self.play_process: Optional[Process] = None
        self.thread = Thread(target=self.consumer, daemon=True, name="CONSUMER")
        self.thread.start()
        self.keyboard_thread = Thread(target=self.keyboard)
        self.keyboard_thread.start()

    def play(self, song):
        self.queue.put((len(self.song_history), song))
        self.song_history.append(song)

    def join(self):
        self.queue.join()

    def play_audio(self, audio: AudioSegment, title):
        data = np.array(audio.get_array_of_samples()[0::2])
        self.ui_thread = Thread(target=self.ui.render, args=[data, audio.max_possible_amplitude, audio.frame_rate,
                                                             title, audio.duration_seconds])
        self.play_process = Process(target=playback.play, args=(audio,))
        self.ui_thread.start()
        self.play_process.start()
        self.started_at = time.time()
        self.play_process.join()
        self.ui_thread.join()

    @staticmethod
    def open_file(song):
        audio = AudioSegment.from_mp3(song)
        title = os.path.basename(song)
        return audio, title

    def play_file(self, song):
        self.play_audio(*self.open_file(song))

    def is_playing(self):
        return self.play_process and self.play_process.is_alive() and self.ui_thread and self.ui_thread.is_alive()

    def stop(self):
        if self.is_playing():
            self.play_process.terminate()
            self.ui.terminate()
            self.play_process.join()
            self.ui_thread.join()

    def pause(self):
        if self.is_playing():
            self.paused = time.time() - self.started_at
            self.stop()

    def restart(self):
        if not self.is_playing() and self.paused:
            audio, title = self.open_file(self.song_history[self.current])
            audio = audio[int(self.paused):]
            self.paused = None
            self.play_audio(audio, title)

    def consumer(self):
        while True:
            if self.paused:
                continue
            index, song = self.queue.get()
            self.current = index
            self.play_file(song)
            self.queue.task_done()

    def keyboard(self):
        while True:
            with self.terminal.cbreak():
                key = self.terminal.inkey()
                if key:
                    if key.name == 'KEY_RIGHT':
                        self.stop()
                    elif key.name == 'KEY_LEFT':
                        if len(self.song_history) > 0:
                            self.stop()
                            self.queue.put((self.current - 1, self.song_history[self.current - 1]))
                            self.queue.put((self.current, self.song_history[self.current]))
                    elif key == ' ':
                        if self.paused:
                            self.restart()
                        else:
                            self.pause()


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

