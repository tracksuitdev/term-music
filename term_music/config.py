import os
from configparser import ConfigParser
from pathlib import Path

UI_SETTINGS = {
    'fps': 60,
    'width': 30,
    'height': 15,
    'print_char': '#',
}

KEYMAP = {
    "KEY_UP": "action_up",
    "KEY_DOWN": "action_down",
    "KEY_LEFT": "action_previous",
    "KEY_RIGHT": "action_next",
    "KEY_ENTER": "action_select",
    "KEY_ESCAPE": "action_exit",
    " ": "action_pause",
    "q": "action_query_mode",
}


class Config:
    def __init__(self, app_dir=os.path.join(Path.home(), ".term-music")):
        self.app_dir = app_dir
        self.config_path = os.path.join(app_dir, "config.ini")
        self.config = ConfigParser()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            print(f"Creating app directory at {app_dir}")
            self.config["general"] = {"download_folder": os.path.join(app_dir, "music-lib")}
            self.config["ui"] = UI_SETTINGS
            self.config["keymap"] = {v: k for k, v in KEYMAP.items()}
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)
            with open(self.config_path, 'w') as f:
                self.config.write(f)

    @property
    def keymap(self):
        return {v: k for k, v in self.config["keymap"].items()}

    @property
    def ui_settings(self):
        if "ui" in self.config["ui"]:
            return {k: int(v) if v.isnumeric() else v for k, v in self.config["ui"].items()}
        else:
            return UI_SETTINGS

    @property
    def download_folder(self):
        return self.config.get("general", "download_folder", fallback=os.path.join(self.app_dir, "music-lib"))
