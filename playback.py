from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
import os

class Playback(BaseWidget):
    def __init__(self, **kwargs):
        super(Playback, self).__init__(**kwargs)
        self.audio = Audio(1)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)
        self.wavs = []
        self.paused = False

    def play_song(self, song):
        parts_list = ['Soprano', 'Alto', 'Tenor', 'Bass']
        files = os.listdir('recordings/' + song)
        for part in parts_list:
            filenames = [f for f in files if part in f]
            biggest_num = 0
            biggest_filename = None
            for file in filenames:
                file_num = int(file[len(part):-4])
                if file_num > biggest_num:
                    biggest_num = file_num
                    biggest_filename = file
                if biggest_filename:
                    self.wavs.append(WaveGenerator(WaveFile('recordings/' + song + '/' + biggest_filename)))

        for wav in self.wavs:
            self.mixer.add(wav)     

    def pause(self):
        self.paused = True

    def on_update(self):
        if not self.paused:
            self.audio.on_update()

