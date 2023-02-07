import time

from audiovisualizer import calc_data_for_visualization, graph_frames_from_audio
from blessed import Terminal
from numpy import ndarray


class UserInterface:

    def __init__(self, terminal: Terminal, fps=30, height=15, width=30, print_char="#"):
        self.fps = fps
        self.width = width
        self.height = height
        self.print_char = print_char
        self.t = terminal
        self.stop = False

    def terminate(self):
        self.stop = True

    def clear_frame(self):
        print(self.t.home + self.t.clear)

    def draw_frame(self, frame, title):
        with self.t.location(0, 0):
            print(title)
            for i, height in enumerate(frame):
                for j in range(height):
                    print(self.t.move_yx(15 - j, i) + self.print_char)


    def render(self, data: ndarray, max_amp: int, frame_rate: int, title: str, duration: float):
        with self.t.hidden_cursor():
            print(self.t.clear)
            length, point_interval, last_frame_length, interval, divisor = \
                calc_data_for_visualization(data, frame_rate, max_amp, self.width, self.fps, self.height)
            elapsed = 0
            start = time.time()
            for i, f in enumerate(graph_frames_from_audio(data, point_interval, self.width, divisor)):
                if self.stop:
                    self.stop = False
                    break
                self.clear_frame()
                self.draw_frame(f, f"{title} {int(elapsed)} / {duration}")
                frame_length = last_frame_length if i == length - 1 else 1  # 1 denotes full frame
                elapsed = ((i + 1 * frame_length) * interval)
                end_time = start + elapsed
                sleep_for = end_time - time.time()
                if sleep_for > 0:
                    time.sleep(sleep_for)
