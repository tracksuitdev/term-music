from threading import Lock

from domain.song import Song


class Data:

    def __init__(self):
        self._current = -1
        self._selected = 0
        self._song_history = []
        self._query_mode = False
        self.selected_lock = Lock()
        self.current_lock = Lock()

    def insert_song_after_current(self, song):
        self._song_history.insert(self._current + 1, song)

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

    def set_query_mode(self, query_mode):
        self._query_mode = query_mode

    def get_query_mode(self):
        return self._query_mode


APP_DATA = Data()


