class Keyboard:

    def __init__(self, data, terminal, keymap):
        self.terminal = terminal
        self.keymap = keymap
        self.data = data
        self.is_blocking = False

    def add_key(self, key, func):
        self.keymap[key] = func

    def remove_key(self, key):
        self.keymap.pop(key)

    def listen(self):
        with self.terminal.cbreak():
            while self.data.has_songs() and not self.data.is_query_mode():
                self.is_blocking = True
                key = self.terminal.inkey()
                self.is_blocking = False
                if key.is_sequence:
                    self.keymap.get(key.name, lambda: None)()
                else:
                    self.keymap.get(key, lambda: None)()

