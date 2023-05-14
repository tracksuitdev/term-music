import time
from queue import Queue, Empty

from pygame import mixer

from app_data import APP_DATA


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
        while APP_DATA.running():
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
                time.sleep(1e-6)
        if mixer.music.get_busy() or self.paused:
            mixer.music.stop()
            mixer.music.unload()
