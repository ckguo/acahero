#pset6.py

# Silent when supposed to be singing
# Singing when supposed to be silent
# Singing wrong pitch
# Singing right pitch

import sys
sys.path.append('..')
from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
from common.gfxutil import *
from common.clock import *
from common.synth import *

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
# from common.kivyparticle import ParticleSystem
from kivy.config import Config

from random import randint, random
import numpy as np
import bisect
from functools import partial

from pitch_detector import *
from display import *

NOW_PIXEL = Window.width*.07 # Pixel of now bar
SCREEN_TIME = 10.0 # Amount of time 
RATE = Window.width/SCREEN_TIME
GAME_HEIGHT = Window.height*.8 # Top of game screen

Config.set('graphics', 'fullscreen', 'auto')
Config.write()

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()
        # Set terminal color to white
        Window.clearcolor = (.8, .8, .8, .8) 

        self.timelabel = topright_label((Window.width * 0.4, Window.height * 0.35))
        self.add_widget(self.timelabel)

        self.scorelabel = topright_label((Window.width * 0.4, Window.height * 0.4))
        self.add_widget(self.scorelabel)

        self.streaklabel = center_label()
        self.add_widget(self.streaklabel)

        self.name = name_label()
        self.add_widget(self.name)

        self.pitchlabel = center_label()
        self.add_widget(self.pitchlabel)

        # for i in range(8):
        #     self.img = Image(source='pink_eighth.png', 
        #                     pos=(randint(0,Window.width),randint(0,Window.height)),  
        #                     keep_ratio=True,
        #                     size_hint_y=None,
        #                     size_hint_x=None,
        #                     height=50,
        #                     color=(random(),random(),random(),random()))
        #     self.add_widget(self.img)

        self.clock = Clock()
        self.clock.stop()
        self.gametime = -SCREEN_TIME
        self.globaltime = self.clock.get_time()
        self.gameon = False

        self.audio = None
        self.audio = AudioController("songs/wdik/wdik-All.wav", "songs/wdik/wdik-Tenor.wav", receive_audio_func=self.receive_audio)

        # Display user's cursor
        self.canvas.add(Color(0,1,0))
        self.user = Triangle(points=[NOW_PIXEL-10, 200-10, NOW_PIXEL-10, 200+10, NOW_PIXEL+20, 200])
        self.canvas.add(self.user)

        self.lanes, self.gem_data, self.barlineData, self.beatData = SongData().read_data('songs/wdik/Tenor.txt', 'songs/wdik/barlines.txt', 'songs/wdik/beats.txt')
        self.display = BeatMatchDisplay(self.lanes, self.gem_data, self.barlineData, self.beatData)
        self.canvas.add(self.display)

        self.player = Player(self.lanes, self.gem_data, self.display, self.audio, PitchDetector())

        # Display screen when starting game. 
        self.name.text = "[color=000000][b]ACAHERO[/b]"
        self.scorelabel.text = "[color=000000]Score: 0"
        self.timelabel.text = "Time: %.2f" % self.gametime
        self.streaklabel.text = "[color=000000][b]keys[/b]\n[i]p:[/i] [size=30]play | pause[/size]\n[i]12345:[/i] [size=30]gems[/size]"
        self.pitchlabel.text = 'correct pitch: %f \n current pitch: %f' % (self.player.correct_pitch, self.player.cur_pitch)

        # # Display particle system? 
        # # load up the particle system, set initial emitter point and start it.
        # self.ps = ParticleSystem('particle/particle.pex')
        # self.ps.emitter_x = NOW_PIXEL
        # self.ps.emitter_y = 0.0
        # self.ps.start()
        # self.add_widget(self.ps)

        self.display.draw_objects()

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.toggle()

        # # button down
        # button_idx = lookup(keycode[1], '12345', (0,1,2,3,4))
        # if button_idx != None:
        #     self.player.on_button_down(button_idx, self.gametime)

    def on_touch_move(self, touch):
        x, y = touch.pos



        # Check if position is near a gem
        self.player.on_touch_move(y, self.gametime)

    def toggle(self):
        self.gameon = not self.gameon
        self.audio.toggle()
        self.display.toggle()
        self.clock.toggle()
        Window.clearcolor = (1, 1, 1, 1) if self.gameon else (.8,.8,.8,.8)


    def endgame(self):
        self.toggle()
        self.timelabel.text = "Game Ended"
        self.streaklabel.text = '[color=CFB53B]Final Score: {}\nLongest Streak: {}'.format(self.player.get_score(), self.player.get_longest_streak())

    def on_update(self) :
        # Only update when gameplay is on
        if self.gameon:
            curr_time = self.clock.get_time()
            dt = curr_time - self.globaltime
            self.gametime += dt
            self.globaltime = curr_time

            self.timelabel.text = "Time: %.2f" % self.gametime
            self.scorelabel.text = 'Score: {}'.format(self.player.get_score())
            self.pitchlabel.text = 'correct pitch: %f \n current pitch: %f' % (self.player.correct_pitch, self.player.cur_pitch)

            # Only display a streak if there is a current streak > 1
            self.streaklabel.text = '[color=CFB53B]{}X Streak'.format(self.player.get_streak()) if self.player.get_streak() > 1 else ''

            self.audio.on_update(self.gametime)
            self.display.on_update(self.gametime, dt)
            self.player.on_update(self.gametime)

            # # End game after 72.8 seconds 
            # if self.gametime > 72.8:
            #     self.endgame()

            # 3,2,1 Start game countdown
            change = SCREEN_TIME/3
            if -change < self.gametime < 0:
                self.streaklabel.text = '1'
            elif -change*2 < self.gametime < -change:
                self.streaklabel.text = '2'
            elif -change*3 < self.gametime < -change*2:
                self.streaklabel.text = '3'

                    # self.ps.emitter_x = x
        
        if not np.round(self.player.cur_pitch) in self.lanes:
            y = 0
        else:
            lane = self.lanes.index(np.round(self.player.cur_pitch))
            y = np.interp(lane, [-1, len(self.lanes)], [0, GAME_HEIGHT])
        # self.ps.emitter_y = y

        # Update the user's cursor
        if y < GAME_HEIGHT:
            self.user.points = [NOW_PIXEL-10, y-10, NOW_PIXEL-10, y+10, NOW_PIXEL+20, y]

    def receive_audio(self, frames, num_channels) :
        # handle 1 or 2 channel input.
        # if input is stereo, mono will pick left or right channel. This is used
        # for input processing that must receive only one channel of audio (RMS, pitch, onset)
        if num_channels == 2:
            mono = frames[0::2] # pick left or right channel
        else:
            mono = frames

        # Microphone volume level, take RMS, convert to dB.
        # display on meter and graph
        rms = np.sqrt(np.mean(mono ** 2))
        rms = np.clip(rms, 1e-10, 1) # don't want log(0)
        db = 20 * np.log10(rms)      # convert from amplitude to decibels 

        # pitch detection: get pitch and display on meter and graph
        self.player.receive_audio(mono)

# creates the Audio control
# creates a song and loads it with solo and bg audio tracks
# creates snippets for audio sound fx
class AudioController(object):
    def __init__(self, bg_path, solo_path, receive_audio_func):
        super(AudioController, self).__init__()
        self.audio = Audio(2, input_func=receive_audio_func)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)

        self.wave_gen_bg = WaveGenerator(WaveFile(bg_path))
        self.wave_gen_solo = WaveGenerator(WaveFile(solo_path))
        self.wave_gen_bg.pause()
        self.wave_gen_solo.pause()

        self.solo_mute = False
        self.mute_time = None

    def start_music(self):
        self.wave_gen_solo.set_gain(1.)
        self.wave_gen_bg.set_gain(0.5)

        self.mixer.add(self.wave_gen_solo)
        self.mixer.add(self.wave_gen_bg)

    # start / stop the song
    def toggle(self):
        self.wave_gen_bg.play_toggle()
        self.wave_gen_solo.play_toggle()

    # mute the solo track
    def mute_solo(self, gametime):
        self.solo_mute = True
        self.mute_time = gametime # Track time to unmute after 0.2 seconds 

    # needed to update audio
    def on_update(self, gametime):
        self.audio.on_update()

        if gametime >= 0.:
            self.start_music()

# holds data for gems and barlines.
class SongData(object):
    def __init__(self):
        super(SongData, self).__init__()
        self.GemDict = {}
        self.BarlineList = []
        self.Lanes = []
        self.BeatList = []

    # read the gems and song data. You may want to add a secondary filepath
    # argument if your barline data is stored in a different txt file.
    def read_data(self, gemFile, barlineFile, beatFile):
    # TODO: figure out how gem and barline data should be accessed...
        gems = open(gemFile, 'r').readlines()
        barlines = open(barlineFile, 'r').readlines()
        beats = open(beatFile, 'r').readlines()

        for i, gem in enumerate(gems):
            if (i==0):
                self.Lanes = [int(x) for x in gem.split(" ")]
                continue

            time, duration, lane, syllable = gem.split("\t")
            self.GemDict.setdefault(int(lane), []).append((float(time), float(duration)))

        for barline in barlines:
            time = barline.strip()
            self.BarlineList.append(float(time))

        for beat in beats:
            time = beat.strip()
            self.BeatList.append(float(time))

        return self.Lanes, self.GemDict, self.BarlineList, self.BeatList


# Handles game logic and keeps score.
# Controls the display and the audio
class Player(object):
    def __init__(self, lanes, gem_data, display, audio_ctrl, pitch_detector):
        super(Player, self).__init__()
        self.lanes = lanes
        self.num_lanes = len(lanes)
        self.display = display
        # self.audio = audio_ctrl

        self.slop_window = 0.1
        self.gem_data = gem_data
        self.gem_idx = [0]*self.num_lanes
        self.gem_status = [[False]*len(gem_data[lane]) for lane in gem_data]
        self.score = 0
        self.streak = 0
        self.longest_streak = self.streak

        self.gem_threshold = 0.25

        self.pitch = pitch_detector
        self.correct_pitch = 0
        self.cur_pitch = 0

    # called by MainWidget
    def on_touch_move(self, y, time):
        # Converts y position to lane integer (zero-indexed)
        lane = np.interp(y,[0,GAME_HEIGHT], [-1,self.num_lanes])
        difference = abs(lane - round(lane))
        lane = int(round(lane)) if difference < self.gem_threshold else False
        
        # if lane:
        #     # Check if there is a gem in that lane at that time / Detect if gem was hit
        #     hit = False
        #     gem_idx = self.gem_idx[lane]

        #     if gem_idx < len(self.gem_data[lane]):
        #         if self.gem_data[lane][gem_idx]-self.slop_window <= time <= self.gem_data[lane][gem_idx]+self.slop_window:
        #             hit = True
        #             self.gem_status[lane][gem_idx] = True
        #             # self.streak += 1
        #             # self.score += 10*self.streak
            
        #     # If button was pressed, but gem was not hit, break the streak.
        #     if not hit:
        #         self.streak = 0

    def get_score(self):
        return self.score 

    def get_streak(self):
        return self.streak

    def get_longest_streak(self):
        return self.longest_streak

    # needed to check if for pass gems (ie, went past the slop window)
    def on_update(self, gametime):
        # Detect if gem was missed / passed
        for lane in range(self.num_lanes):
            gem_idx = self.gem_idx[lane]

            if lane in self.gem_data and gem_idx < len(self.gem_data[lane]):
                gem_time, duration = self.gem_data[lane][gem_idx]

                if gem_time < gametime < gem_time + duration:
                    self.correct_pitch = self.lanes[lane]

                if gametime > gem_time + duration:
                    self.correct_pitch = 0
                    self.gem_idx[lane] += 1

                    # If the gem was not hit, then play missed sfx, mute solo, change colors, and reset the streak
                    # if not self.gem_status[lane][gem_idx]: 
                    #     self.audio.play_sfx()
                    #     self.audio.mute_solo(gametime)
                    #     self.display.gem_pass(lane)
                    #     self.streak = 0

        # # Update longest streak
        # if self.longest_streak < self.streak:
        #     self.longest_streak = self.streak


    def receive_audio(self, mono):
        self.cur_pitch = self.pitch.write(mono)
        fs = 44100.
        if np.round(self.cur_pitch) == self.correct_pitch:
            if np.round(self.cur_pitch) == 0:
                self.score += 0.1*len(mono)/fs
            else:
                self.score += len(mono)/fs
        elif self.correct_pitch == 0 or self.cur_pitch == 0:
            self.score -= 0.5*len(mono)/fs
        else:
            self.cur_pitch -= 0.5*len(mono) * (np.round(self.cur_pitch) - self.correct_pitch)/fs

run(MainWidget)
