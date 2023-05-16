#!/usr/bin/python3
import os
import traceback
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from term_music.commands import Commands

import argparse

from term_music.config import Config

version = '0.1.0'


def main():
    try:
        config = Config()
    except Exception:
        traceback.print_exc()
        print(f"Error loading config, exiting...")
        return

    parser = argparse.ArgumentParser(prog="music",
                                     description="Music player and library manager. "
                                                 "Starts the player in no songs mode if no arguments are given.")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {version}")

    subparsers = parser.add_subparsers(dest="command")
    parser_play = subparsers.add_parser("play", help="play a song")
    parser_play.add_argument("query", nargs="+",
                             help="query used to search the library or youtube for the song to play")
    parser_play.add_argument("-e", "--exact", action="store_true",
                             help="only use exact matches to play a song from library, will not search youtube or "
                                  "download a song")
    parser_play.add_argument("-nd", "--nodownload", action="store_true",
                             help="don't search youtube and download the song if none is found in library")

    parser_playall = subparsers.add_parser("playall", help="play all songs or playlists")
    parser_playall.add_argument("what", nargs="?", default="songs", choices=["songs", "playlists"])

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
    parser_load.add_argument("-p", "--playlist", help="name of the playlist that will be made out of downloaded songs")
    parser_load.add_argument("-c", "--check", help="if true will check if song already exists and won't download it",
                             action="store_true")

    args = parser.parse_args()
    commands = Commands(config)
    commands.run_command(args.command, args)


if __name__ == "__main__":
    main()
