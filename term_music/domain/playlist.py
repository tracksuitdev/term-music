import os


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
