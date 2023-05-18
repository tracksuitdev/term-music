import traceback

from term_music.domain.playlist import Playlist
from term_music.app_data import APP_DATA
from term_music.app import App
from term_music.config import Config
from term_music.domain.music_library import MusicLibrary


def generalized_search(search_func, query):
    for x in search_func(query):
        print(x)


class Commands:

    def __init__(self, config: Config):
        self.lib = MusicLibrary(APP_DATA, config.download_folder)
        self.app = App(APP_DATA, self.lib, config)

    def run_command(self, command, args):
        if command is None:
            self.app.run()
        else:
            getattr(self, command)(args)

    def search(self, args):
        if "songs" == args.type or args.type is None:
            generalized_search(self.lib.search_song, args.query)
        if "playlists" == args.type or args.type is None:
            generalized_search(self.lib.search_playlists, args.query)

    def play(self, args):
        if args.exact:
            for q in args.query:
                self.lib.play_song(q)
        elif args.nodownload:
            for q in args.query:
                self.lib.play_song(self.lib.search_song(q)[0])
        else:
            for q in args.query:
                self.lib.download_and_play_song(q)
        self.app.run()

    def playall(self, args):
        if args.what == "songs":
            self.lib.play_all()
        else:
            self.lib.play_all_playlists()
        self.app.run()

    def playlist(self, args):
        if args.exact:
            self.lib.play_playlist(args.query)
        else:
            self.lib.search_and_play_playlist(args.query)
        self.app.run()

    def ls(self, args):
        if args.all:
            [print(s) for s in self.lib.songs()]
            [print(p) for p in self.lib.playlists()]
        elif args.full:
            self.lib.print_songs_and_playlists()
        elif args.playlist:
            [print(p) for p in self.lib.get_all_playlists()]
        else:
            [print(s) for s in self.lib.songs()]

    def load(self, args):
        new_playlist = self.lib.get_or_create_playlist(Playlist.filename(args.playlist)) if args.playlist else None
        for i, s in enumerate(args.songs):
            try:
                song_title = self.lib.search_and_download(s, args.check)
                if new_playlist:
                    new_playlist.add_song(song_title)
            except Exception:
                traceback.print_exc()
            print(f"Processed {i + 1}/{len(args.songs)}")
        if new_playlist:
            new_playlist.save()
