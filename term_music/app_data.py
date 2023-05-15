from enum import Enum
from threading import Lock

from term_music.domain.song import Song


class Mode(Enum):
    NORMAL = 1
    QUERY = 2


class Data:

    def __init__(self):
        self._current = -1
        self._selected = 0
        self._song_history = []
        self._running = True
        self._mode = Mode.NORMAL
        self.selected_lock = Lock()
        self.current_lock = Lock()

    def insert_song_after_current(self, song):
        self.current_lock.acquire()
        self._song_history.insert(self._current + 1, song)
        self.current_lock.release()

    def restart_current(self):
        self.current_lock.acquire()
        self._current = -1
        self.current_lock.release()

    def reset_current(self):
        self.current_lock.acquire()
        self._current = self.length() - 1
        self.current_lock.release()

    def length(self):
        return len(self._song_history)

    def add_song(self, song):
        self._song_history.append(song)

    def get_current(self):
        return self._current

    def end(self):
        self.quit()
        self.set_current(self.length())

    def has_songs(self):
        self.current_lock.acquire()
        has_songs = self.length() > 0 and self._current < self.length()
        self.current_lock.release()
        return has_songs

    def inc_current(self):
        self.current_lock.acquire()
        if self._current >= self.length():
            self.current_lock.release()
            return False
        self._current += 1
        self.current_lock.release()
        return self._current < self.length()

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

    def query_mode(self):
        print("QUERY MODE")
        self._mode = Mode.QUERY

    def normal_mode(self):
        self._mode = Mode.NORMAL

    def is_query_mode(self):
        return self._mode == Mode.QUERY

    def running(self):
        return self._running

    def quit(self):
        self._running = False


APP_DATA = Data()
