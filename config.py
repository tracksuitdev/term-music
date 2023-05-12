import os

DOWNLOAD_FOLDER = os.path.join("/home", "ivan", "music-lib")

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
