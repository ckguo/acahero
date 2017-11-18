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
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from common.kivyparticle import ParticleSystem
from kivy.config import Config

from random import randint, random
import numpy as np
import bisect
from functools import partial

NOW_PIXEL = 60 # Pixel of now bar
SCREEN_TIME = 3.0 # Amount of time 
GAME_HEIGHT = Window.height - 100 # Top of game screen

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
        self.audio = AudioController("songs/wdik/wdik-All.wav", "songs/wdik/wdik-Tenor.wav")

        self.lanes, self.gem_data, self.barlineData = SongData().read_data('songs/wdik/Tenor.txt', 'songs/wdik/barlines.txt')
        self.display = BeatMatchDisplay(self.lanes, self.gem_data, self.barlineData)
        self.canvas.add(self.display)

        self.player = Player(self.lanes, self.gem_data, self.display, self.audio)

        # Display screen when starting game. 
        self.name.text = "[color=000000][b]ACAHERO[/b]"
        self.scorelabel.text = "[color=000000]Score: 0"
        self.timelabel.text = "Time: %.2f" % self.gametime
        self.streaklabel.text = "[color=000000][b]keys[/b]\n[i]p:[/i] [size=30]play | pause[/size]\n[i]12345:[/i] [size=30]gems[/size]"

        # Display user's cursor
        self.canvas.add(Color(0,1,0))
        self.user = Triangle(points=[NOW_PIXEL-5, 0-10, NOW_PIXEL-5, 0+10, NOW_PIXEL+15, 0])
        self.canvas.add(self.user)
        
        # Display particle system? 
        # load up the particle system, set initial emitter point and start it.
        self.ps = ParticleSystem('particle/particle.pex')
        self.ps.emitter_x = NOW_PIXEL
        self.ps.emitter_y = 0.0
        self.ps.start()
        self.add_widget(self.ps)

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

        # self.ps.emitter_x = x
        self.ps.emitter_y = y

        # Update the user's cursor
        if y < GAME_HEIGHT:
            self.canvas.remove(self.user)
            self.canvas.add(Color(0,1,0))
            self.user = Triangle(points=[NOW_PIXEL-5, y-10, NOW_PIXEL-5, y+10, NOW_PIXEL+15, y])
            self.canvas.add(self.user)

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

# creates the Audio control
# creates a song and loads it with solo and bg audio tracks
# creates snippets for audio sound fx
class AudioController(object):
    def __init__(self, bg_path, solo_path):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
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

    # read the gems and song data. You may want to add a secondary filepath
    # argument if your barline data is stored in a different txt file.
    def read_data(self, gemFile, barlineFile):
    # TODO: figure out how gem and barline data should be accessed...
        gems = open(gemFile, 'r').readlines()
        barlines = open(barlineFile, 'r').readlines()

        for i, gem in enumerate(gems):
            if (i==0):
                self.Lanes = gem.split(" ")
                continue

            time, duration, lane = gem.split("\t")
            self.GemDict.setdefault(int(lane), []).append((float(time), float(duration)))

        for barline in barlines:
            time = barline.strip()
            self.BarlineList.append(float(time))

        return self.Lanes, self.GemDict, self.BarlineList

# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color, length):
        super(GemDisplay, self).__init__()  
        self.rectcolor = color
        self.circolor = Color(color.r, color.g, color.b, 1)
        self.pos = pos
        self.length = length
        self.draw_gem()

    def draw_gem(self):
        # Draw rectangle
        self.add(self.rectcolor)
        self.gem = Rectangle( pos=(self.pos[0], self.pos[1]-10), size=(self.length, 20) )
        self.add(self.gem)

        self.add(self.circolor)
        self.circle = CEllipse( cpos=(self.pos), size=(20,20), segments = 10 )
        self.add(self.circle)

        # # Draw music note
        # self.add(Color(0,0,0))
        # self.circle = CEllipse( cpos=(self.pos), size=(36,36), segments = 10 )
        # self.add(self.circle)
        # self.line = Line(points=[self.pos[0]+14, self.pos[1], self.pos[0]+14, self.pos[1]+45], width=4)
        # self.add(self.line)

    # change to display this gem being hit
    def on_hit(self):
        # Gem is removed when hit.
        pass 

    # change to display a passed gem
    def on_pass(self):
        # Gem color is changed to grey.
        self.color = Color(.8,.8,.8)
        self.remove(self.gem)
        self.draw_gem()

    def translate(self, dx):
        newx = self.pos[0] - dx
        self.pos = (newx, self.pos[1])

        self.remove(self.circle)
        self.remove(self.gem)
        self.draw_gem()

        return newx+self.length > 0

    def get_x(self):
        return self.pos[0]

class Pop(InstructionGroup) :
    def __init__(self, pos, color):
        super(Pop, self).__init__()

        self.color = color
        self.color.a = 0.2
        self.add(self.color)

        self.circle = CEllipse(cpos = pos)
        self.add(self.circle)

        r = 45 # Initial radius

        # create keyframe animation: a frame is: (time, alpha radius)
        self.anim = KFAnim((0,   1, r),
                           (0.4, 0, r/2),)

        self.time = 0
        self.on_update(0)

    def on_update(self, dt):
        values = self.anim.eval(self.time)
        self.color.a = values[0]
        self.circle.csize = values[1] * 2, values[1] * 2
        self.time += dt

        return self.anim.is_active(self.time)

# Displays one button on the nowbar
class ButtonDisplay(InstructionGroup):
    def __init__(self, pos, color):
        super(ButtonDisplay, self).__init__()
        self.color = color
        self.pos = pos
        self.draw_button()

    def draw_button(self):
        self.add(self.color)
        self.button = CEllipse( cpos=self.pos, size=(15,25), segments = 10 )
        self.add(self.button)

    # displays when button is down (and if it hit a gem)
    def on_down(self, hit):
        self.color.a -= .5

    # back to normal state
    def on_up(self):
        self.color.a += .5

class Barline(InstructionGroup):
    def __init__(self, x):
        super(Barline, self).__init__()

        self.points = [[x, 0],[x, GAME_HEIGHT]]
        self.draw_line()

    def draw_line(self):
        self.barline = Line(points=self.points, width=3)
        self.add(Color(0,0,0))
        self.add(self.barline)

    def translate(self, dx):
        newx = self.points[0][0] - dx
        self.points[0][0] = newx
        self.points[1][0] = newx
            
        self.remove(self.barline)
        self.draw_line()

        return newx > 0

# Displays and controls all game elements: Nowbar, Buttons, BarLines, Gems.
class BeatMatchDisplay(InstructionGroup):
    def __init__(self, lanes, gem_data, barline_data):
        super(BeatMatchDisplay, self).__init__()
        self.lanes = lanes
        self.num_lanes = len(lanes)

        # Colors corresponding to each lane
        self.colors = [Color(1,.5,0,.4)]*self.num_lanes

        # To keep track of next gems
        self.gem_data = gem_data
        self.gem_idx = [0]*self.num_lanes
        self.gems = [[] for i in range(self.num_lanes)]

        # To keep track of next barline
        self.barline_data = barline_data
        self.barline_idx = 0
        self.barlines = []

        # Draw header 
        self.add(Color(0,0,0))
        self.header = Rectangle(pos=(0, GAME_HEIGHT), size=(Window.width, 10))
        self.add(self.header)

        # Draw nowbar
        self.nowbar = Rectangle(pos=(NOW_PIXEL, 0), size=(10, GAME_HEIGHT))
        self.add_nowbar()

        # Draw gem lanes
        self.lines = [Line(points=[(Window.width, np.interp(y, [-1,self.num_lanes], [0,GAME_HEIGHT])), (0, np.interp(y, [-1,self.num_lanes], [0,GAME_HEIGHT]))], width=0.4) for y in range(self.num_lanes)]      
        self.add_lines()

        # # Draw buttons
        # self.buttons = [ButtonDisplay((NOW_PIXEL+5, np.interp(y, [-1,self.num_lanes], [0,GAME_HEIGHT])), self.colors[y]) for y in range(self.num_lanes)]
        # self.add_buttons()

        self.pops = AnimGroup() # Animations after gems are hit.
        self.add(self.pops)

        self.paused = True

    def toggle(self):
        self.paused = not self.paused 

        if self.paused:
            self.add(Color(.83,.83,.83))

    def add_nowbar(self):
        self.add(Color(.3,.3,.3,.2))
        self.add(self.nowbar)

    def add_lines(self):
        self.add(Color(.4,.4,.4))
        for line in self.lines:
            self.add(line)

    def add_buttons(self):
        for button in self.buttons:
            self.add(button)

    def draw_barline(self):
        barline = Barline(Window.width)
        self.add(barline)
        self.barlines.append(barline)

    def draw_gem(self, lane, y, duration):
        length = ((Window.width - (NOW_PIXEL+5))/SCREEN_TIME) * duration
        gem = GemDisplay(pos=(Window.width, y), color=self.colors[lane], length=length)
        self.add(gem)
        self.gems[lane].append(gem)

    # called by Player. Causes the right thing to happen
    def gem_hit(self, gem_idx, lane):
        gem = self.gems[lane][gem_idx]

        # Add pop animation.
        self.pop = Pop(gem.pos, gem.color)
        self.pops.add(self.pop)

        # Remove from canvas and gems list
        self.remove(gem) 
        self.gems[lane].remove(gem)
        
    # called by Player. Causes the right thing to happen
    def gem_pass(self, lane):
        # Assume that the first gem in the lane just passed
        gem_idx = 0
        gem = self.gems[lane][gem_idx]
        gem.on_pass()

    # called by Player. Causes the right thing to happen
    def on_button_down(self, lane):
        pass

        # if hit: 
        #     try:
        #     # Assume that the user was aiming for the gem that is located the closest to the nowbar.
        #         dists = [abs(gem.get_x() - self.nowbar.pos[1]) for i, gem in enumerate(self.gems[lane])]
        #         gem_idx = np.argmin(dists)
        #         self.gem_hit(gem_idx, lane)
        #     except:
        #         pass
        #     #     print(self.gems[lane], "\n", lane, "\n")

    # called by Player. Causes the right thing to happen
    def on_button_up(self, lane):
        button = self.buttons[lane]
        button.on_up()

    # call every frame to make gems and barlines flow down the screen
    def on_update(self, gametime, dt) :
        dy = ((Window.width - (NOW_PIXEL+5))/SCREEN_TIME) * dt 

        # Schedule to create new barlines
        if self.barline_idx < len(self.barline_data):
            if self.barline_data[self.barline_idx]-SCREEN_TIME <= gametime:
                self.draw_barline()
                self.barline_idx += 1

        # Update barlines 
        killList = []
        for barline in self.barlines:
            if not self.paused:
                alive = barline.translate(dy)
                if not alive: killList.append(barline)

        # Schedule to create gems per lane
        for lane in range(self.num_lanes):
            gem_idx = self.gem_idx[lane]
            if lane in self.gem_data and gem_idx < len(self.gem_data[lane]):
                gem_time, duration = self.gem_data[lane][gem_idx]
        
                if gem_time-SCREEN_TIME <= gametime:
                    y = np.interp(lane, [-1,self.num_lanes], [0,GAME_HEIGHT])
                    self.draw_gem(lane, y, duration)
                    self.gem_idx[lane] += 1

        # Update gems
        for lane in range(self.num_lanes):
            for gem in self.gems[lane]:
                if not self.paused:
                    alive = gem.translate(dy)
                    if not alive: killList.append((lane, gem))
            
        # Remove barline/gems from canvas if they are off screen.
        for obj in killList:
            if isinstance(obj, tuple):
                lane, gem = obj
                self.remove(gem) 
                self.gems[lane].remove(gem)
            else:
                self.remove(obj) 
                self.barlines.remove(obj)

        self.pops.on_update()

# Handles game logic and keeps score.
# Controls the display and the audio
class Player(object):
    def __init__(self, lanes, gem_data, display, audio_ctrl):
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

        self.display.on_button_down(lane)

    def get_score(self):
        return self.score 

    def get_streak(self):
        return self.streak

    def get_longest_streak(self):
        return self.longest_streak

    # needed to check if for pass gems (ie, went past the slop window)
    def on_update(self, gametime):
        # Detect if gem was missed / passed
        # for lane in range(5):
        #     gem_idx = self.gem_idx[lane]

        #     if lane in self.gem_data and gem_idx < len(self.gem_data[lane]):
        #         gem_time, duration = self.gem_data[lane][gem_idx]

        #         if gem_time+self.slop_window < gametime:
        #             self.gem_idx[lane] += 1

        #             # If the gem was not hit, then play missed sfx, mute solo, change colors, and reset the streak
        #             if not self.gem_status[lane][gem_idx]: 
        #                 self.audio.play_sfx()
        #                 self.audio.mute_solo(gametime)
        #                 self.display.gem_pass(lane)
        #                 self.streak = 0

        # # Update longest streak
        # if self.longest_streak < self.streak:
        #     self.longest_streak = self.streak

        pass

run(MainWidget)
