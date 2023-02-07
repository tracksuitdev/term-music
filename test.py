from blessed import Terminal

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

which_key_is_it()
