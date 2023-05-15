import os
from typing import Iterable

import youtube_dl

from term_music.domain.playlist import Playlist


def is_song(filename):
    return filename and filename.endswith(".mp3")


def is_playlist(filename):
    return filename and filename.endswith(".txt")


def remove_extension(filenames):
    return [f[:-4] for f in filenames]


def search(query: str, data: Iterable[str]):
    lower_query = query.lower()
    results = []
    for item in data:
        if lower_query in item.lower():
            results.append(item)
    return results


class MusicLibrary:
    def __init__(self, data, download_folder):
        self.download_folder = download_folder
        self.data = data
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
        return search(search_query, self.songs())

    def search_playlists(self, search_query):
        return search(search_query, self.playlists())

    def search_and_play_playlist(self, search_query):
        self.play_playlist_filename(self.search_playlists(search_query)[0])

    def search_and_download(self, song_query, check=False, ask=False):
        ydl_opts = {
            "default_search": "ytsearch",
            "max_downloads": 1,
            "format": "bestaudio/best",
            "noplaylist": True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_query, download=False)
            song_title = info["entries"][0]["title"]
            if ask:
                ans = input(f"Do you want to download {song_title} Y/N: ")
                if ans == "N":
                    return None
            if check and song_title in self.songs():
                # don't download if we already have one
                print(f"Skipped download of {song_title}")
                return song_title
            song_url = info["entries"][0]["webpage_url"]
            # Download the song
            self.download_song(song_url)
            return song_title

    def download_and_play_song(self, song_query, now=False, ask=False):
        # Search the local music library for the song
        search_result = self.search_song(song_query)
        if search_result:
            # Found the song in the local library
            song_title = search_result[0]
        else:
            song_title = self.search_and_download(song_query, ask=ask)

        if not song_title:
            return False

        # Play the song
        self.play_song(song_title, now)
        return True

    def play_filename(self, filename, now=False):
        """
        Adds filename to player queue, if now is True the song is added after the current one
        """
        full_path = os.path.join(self.download_folder, filename)
        if now:
            self.data.insert_song_after_current(full_path)
        else:
            self.data.add_song(full_path)

    def play_song(self, song: str, now=False):
        self.play_filename(song + ".mp3", now)

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