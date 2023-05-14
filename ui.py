import logging
import os.path
import time

import numpy as np
from blessed import Terminal
from pydub import AudioSegment
from pygame import mixer

logger = logging.getLogger(__name__)


class UserInterface:

    def __init__(self, data, terminal: Terminal, fps=60, height=15, width=30, print_char="#"):
        self.data = data
        self.fps = fps
        self.width = width
        self.height = height
        self.print_char = print_char
        self.t = terminal
        self.stop = False
        self.paused = False
        self.skipped_frames = 0
        self.interval = 1 / fps

    @staticmethod
    def format_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return "%d:%02d:%02d" % (h, m, s)
        return "%d:%02d" % (m, s)

    def terminate(self):
        self.stop = True

    def pause(self):
        self.paused = True

    def unpause(self):
        self.stop = False
        self.paused = False

    def clear(self):
        print(self.t.home + self.t.clear)

    def draw_frame(self, frame):
        for i, height in enumerate(frame):
            for j in range(int(height)):
                print(self.t.move_yx(self.height - j - 1, i) + self.print_char)

    def draw_song_list(self, duration, elapsed):
        max_width = self.t.width - self.width
        start = (self.data.get_selected() // self.height) * self.height
        end = min(start + self.height, self.data.length())
        for i in range(start, end):
            song = self.data.path_at(i)
            title = os.path.basename(song)
            with self.t.location(self.width, i - start):
                if self.data.get_current() == i:
                    clock_str = f" {elapsed}/{duration}"
                    print(self.t.green(title[:max_width - len(clock_str)] + clock_str))
                elif self.data.get_selected() == i:
                    print(self.t.blue(title[:max_width]))
                else:
                    print(self.t.snow4(title[:max_width]))

    def get_frames(self, segment: AudioSegment):
        data = np.frombuffer(segment.raw_data, dtype=np.int16)
        x = np.linspace(0, data.size - 1, int(segment.duration_seconds * self.fps * self.width))
        xp = np.linspace(0, data.size - 1, data.size)
        frames = np.ceil(np.abs(np.interp(x, xp, data)) * (self.height / segment.max_possible_amplitude))
        return frames

    def render(self, frames, duration: float):
        with self.t.hidden_cursor():
            print(self.t.clear)
            current_frame = 0
            duration_str = self.format_time(duration)
            while not self.stop and self.data.running() and ((current_frame * self.width) < len(frames)):
                frame_start = time.time()
                elapsed_str = self.format_time(min(mixer.music.get_pos() / 1000, duration))
                self.clear()
                if not self.paused:
                    f = frames[current_frame * self.width:(current_frame + 1) * self.width]
                    self.draw_frame(f)
                    current_frame += 1
                self.draw_song_list(duration_str, elapsed_str)
                sleep_for = frame_start + self.interval - time.time()
                if sleep_for > 0:
                    time.sleep(sleep_for)
                else:
                    self.skipped_frames += 1
        self.stop = False
        self.paused = False
