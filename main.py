#!/usr/bin/python3

import argparse

from config import DOWNLOAD_FOLDER
from music_library import MusicLibrary, Playlist


def play_song(music_lib: MusicLibrary, args):
    if args.exact:
        for q in args.query:
            music_lib.play_song(q)
    elif args.nodownload:
        for q in args.query:
            music_lib.play_song(music_lib.search_song(q)[0])
    else:
        for q in args.query:
            music_lib.download_and_play_song(q)


def play_all(music_lib: MusicLibrary, args):
    if args.what == "songs":
        music_lib.play_all()
    else:
        music_lib.play_all_playlists()


def playlist(music_lib: MusicLibrary, args):
    if args.exact:
        music_lib.play_playlist(args.query)
    else:
        music_lib.search_and_play_playlist(args.query)


def ls(music_lib: MusicLibrary, args):
    if args.all:
        [print(s) for s in music_lib.songs()]
        [print(p) for p in music_lib.playlists()]
    elif args.full:
        music_lib.print_songs_and_playlists()
    elif args.playlist:
        [print(p) for p in music_lib.get_all_playlists()]
    else:
        [print(s) for s in music_lib.songs()]


def load(music_lib: MusicLibrary, args):
    new_playlist = Playlist(music_lib.download_folder, args.playlist) if args.playlist else None
    for s in args.songs:
        song_title = music_lib.search_and_download(s)
        if new_playlist:
            new_playlist.add_song(song_title)
    if new_playlist:
        new_playlist.save()


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(prog="music")

    # Create the sub-parsers
    subparsers = parser.add_subparsers(dest="command")
    parser_play = subparsers.add_parser("play", help="play a song")
    parser_play.add_argument("query", nargs="+", help="query used to search the library or youtube for the song to play")
    parser_play.add_argument("-e", "--exact", action="store_true",
                             help="only use exact matches to play a song from library, will not search youtube or "
                                  "download a song")
    parser_play.add_argument("-nd", "--nodownload", action="store_true",
                             help="don't search youtube and download the song if none is found in library")

    parser_playall = subparsers.add_parser("playall", help="play all songs or playlists")
    parser_playall.add_argument("what", nargs="*", default="songs", choices=["songs", "playlists"])

    parser_playlist = subparsers.add_parser("playlist", help="play playlist")
    parser_playlist.add_argument("query", help="query used to search the library for a playlist to play")
    parser_playlist.add_argument("-e", "--exact", action="store_true", help="only play a playlist if exact match is "
                                                                            "found")

    parser_list = subparsers.add_parser("ls", help="list songs")
    parser_list.add_argument("-a", "--all", action="store_true", help="list all songs and playlists")
    parser_list.add_argument("-p", "--playlist", action="store_true", help="list only playlists")
    parser_list.add_argument("-f", "--full", action="store_true", help="list all songs with playlists they are on")

    parser_load = subparsers.add_parser("load", help="download a list of songs")
    parser_load.add_argument("songs", nargs="+", help="list of songs to download in music library")
    parser_load.add_argument("-p", "--playlist", help="name of the playlist that will be made out of downloaded songs",
                             dest="make")


    # Parse the command line arguments
    args = parser.parse_args()

    # Create a new music library
    library = MusicLibrary(DOWNLOAD_FOLDER)

    # Handle the different commands
    if args.command == "play":
        # Play the given song or playlist
        play_song(library, args)
    elif args.command == "playall":
        play_all(library, args)
    elif args.command == "playlist":
        playlist(library, args)
    elif args.command == "ls":
        ls(library, args)
    elif args.command == "load":
        load(library, args)


if __name__ == "__main__":
    main()

