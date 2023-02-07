import time

from blessed import Terminal
from pygame import mixer

from ui import UserInterface
import numpy as np

def ui_test():
    ui = UserInterface(Terminal())

    data = np.random.randint(0, 50, size=1_000_000)
    ui.render(data, 50, 900, "song", 1_000_000 / 900)

def which_key_is_it():
    terminal = Terminal()
    with terminal.cbreak():
        key = terminal.inkey()
        print(key)
        print(key.name)
        print(key.code)


def mixing():
    mixer.init()
    mixer.music.load("/home/ivan/music-lib/Nuclear.mp3")
    mixer.music.play()
    while mixer.music.get_busy():
        print(mixer.music.get_pos())
        time.sleep(10)

mixing()
