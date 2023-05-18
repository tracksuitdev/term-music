import os.path
from typing import Iterable


def is_song(filename):
    return filename and filename.endswith(".mp3")


def is_playlist(filename):
    return filename and filename.endswith(".txt")


def remove_extension(filenames):
    return [f[:-4] for f in filenames]


def name_from_filename(filename):
    return os.path.basename(filename)[:-4]


def search(query: str, data: Iterable[str]):
    lower_query = query.lower()
    results = []
    for item in data:
        if lower_query in item.lower():
            results.append(item)
    return results
