from common.gfxutil import *

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from common.kivyparticle import ParticleSystem

import numpy as np

NOW_PIXEL = Window.width*.07 # Pixel of now bar
SCREEN_TIME = 10.0 # Amount of time 
RATE = Window.width/SCREEN_TIME
GAME_HEIGHT = Window.height*.8 # Top of game screen

def lane_to_y_pos(lane, num_lanes):
    return np.interp(lane, [-1,num_lanes], [0,GAME_HEIGHT])

# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color, length, lyric=False):
        super(GemDisplay, self).__init__()  
        self.rectcolor = color
        self.circolor = Color(color.r, color.g, color.b, 1)
        self.pos = pos
        self.length = length
        self.lyric = lyric
        self.draw_gem()

    def draw_gem(self):
        if self.lyric:
            # Draw lyric
            self.add(Color(256, 256, 256))
            texture = CoreImage('./lyrics/' + self.lyric + '.png').texture
            self.text = Rectangle( pos=(self.pos[0]+10, self.pos[1]+10), size=(100, 50), texture=texture )
            self.add(self.text)

        # Draw rectangle
        self.add(self.rectcolor)
        self.gem = Rectangle( pos=(self.pos[0], self.pos[1]-10), size=(self.length, 20) )
        self.add(self.gem)

        # Draw circle
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

class Barline(InstructionGroup):
    def __init__(self, x, width, color):
        super(Barline, self).__init__()
        self.points = [[x, 0],[x, GAME_HEIGHT]]
        self.barline = Line(points=self.points, width=width)
        self.add(color)
        self.add(self.barline)

class HealthBar(InstructionGroup):
    def __init__(self):
        super(HealthBar, self).__init__()
        self.redbar = Line(points=[Window.width*0.85, Window.height*0.93, Window.width*0.95, Window.height*0.93], width=12)
        self.add(Color(.9,.3,.3,0.5))
        self.add(self.redbar)
        self.greenbar = Line(points=[Window.width*0.85, Window.height*0.93, Window.width*(0.95), Window.height*0.93], width=12)
        self.add(Color(.1,1.0,.4,0.5))
        self.add(self.greenbar)

    def add_healthbar(self, score):
        self.greenbar.points = [Window.width*0.85, Window.height*0.93, Window.width*(0.85+0.1*min(score, 1.0)), Window.height*0.93]

    def on_update(self, score):
        self.add_healthbar(score)


# Displays and controls all game elements: Nowbar, Buttons, BarLines, Gems.
class BeatMatchDisplay(InstructionGroup):
    def __init__(self, lanes, gem_data, barline_data, beat_data, ps):
        super(BeatMatchDisplay, self).__init__()
        self.lanes = lanes
        self.num_lanes = len(lanes)

        # Colors corresponding to each lane
        self.colors = [Color(1,.5,0,.4)]*self.num_lanes

        self.gem_data = gem_data
        self.barline_data = barline_data
        self.beat_data = beat_data
        
        # Dictionary that stores the current color of the gems.
        self.action_colors = self.initialize_action_colors()

        self.add_header()
        self.add_nowbar()
        self.add_lines() # Add gem lines

        self.pops = AnimGroup() # Animations after gems are hit.
        self.add(self.pops)

        self.ps = ps

        self.paused = True

    def initialize_action_colors(self):
        # Pass Color: Gray Color(.8,.8,.8)
        action_colors = {}

        for lane in self.gem_data:
            num_gems = len(self.gem_data[lane])
            action_colors[lane] = [[Color(0.,0.,0.), 0] for i in range(num_gems)]

        return action_colors

    def draw_objects(self):
        self.trans = Translate()
        self.trans.x = Window.width + NOW_PIXEL
        self.add(self.trans)

        for beat in self.beat_data:
            self.draw_bar(beat*RATE, 1.5, Color(0, 0, 0.7, mode='hsv'))
        for bar in self.barline_data:
            self.draw_bar(bar*RATE, 3, Color(0, 0, 0))
        
        for lane in range(self.num_lanes):
            for gem_time, duration, lyric in self.gem_data[lane]:
                self.draw_gem(gem_time*RATE, lane, duration, lyric)

    def toggle(self):
        self.paused = not self.paused 

        if self.paused:
            self.add(Color(.83,.83,.83))

    def add_header(self):
        self.add(Color(0,0,0))
        self.header = Rectangle(pos=(0, GAME_HEIGHT), size=(Window.width, 10))
        self.add(self.header)

    def add_nowbar(self):
        self.nowbar = Rectangle(pos=(NOW_PIXEL, 0), size=(10, GAME_HEIGHT))
        self.add(Color(.3,.3,.3,.2))
        self.add(self.nowbar)

    def add_lines(self):
        self.lines = [Line(points=[(Window.width, lane_to_y_pos(y, self.num_lanes)), (0, lane_to_y_pos(y, self.num_lanes))], width=0.4) for y in range(self.num_lanes)]      
        self.add(Color(.4,.4,.4))
        for line in self.lines:
            self.add(line)

    def draw_bar(self, x_pos, width, color):
        barline = Barline(x_pos, width, color)
        self.add(barline)

    def draw_gem(self, x_pos, lane, duration, lyric):
        y = lane_to_y_pos(lane, self.num_lanes)
        length = RATE * duration 

        gem = GemDisplay(pos=(x_pos, y), color=self.colors[lane], length=length, lyric=lyric)
        self.add(gem)

    # Called by Player.
    def animate_action(self, action, current_gem):
        # pass: Silent when supposed to be singing
        # miss: Singing when supposed to be silent
        # silent: Correctly silent
        # off: Singing wrong pitch
        # on: Singing right pitch

        if not current_gem: return

        lane, gem_idx = current_gem
        gem_time, duration, lyric = self.gem_data[lane][gem_idx]
        x = gem_time*RATE
        y = lane_to_y_pos(lane, self.num_lanes)
        length = (NOW_PIXEL+10) - (x + self.trans.x)
        
        print('before: {}'.format(self.action_colors[lane][gem_idx][1]))
        self.action_colors[lane][gem_idx][1] += 1
        color, denom = self.action_colors[lane][gem_idx]
        print('after: {}'.format(self.action_colors[lane][gem_idx][1]))             
        
        if action == 'pass':
            color.r = (color.r+0.1)/denom
            color.g = (color.g+0.)/denom
            color.b = (color.b+0.)/denom
        elif action == 'on':
            color.r = (color.r+0.)/denom
            color.g = (color.g+0.1)/denom
            color.b = (color.b+0.)/denom
        elif action == 'off':
            color.r = (color.r+0.1)/denom
            color.g = (color.g+0)/denom
            color.b = (color.b+0.)/denom

        # Normalize color to be within 0-1
        max_val = max(color.r, color.g, color.b)
        color.r = color.r/max_val
        color.g = color.g/max_val
        color.b = color.b/max_val

        gem = GemDisplay(pos=(x, y), color=color, length=length, lyric=False)
        self.add(gem)

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

    # call every frame to make gems and barlines flow down the screen
    def on_update(self, gametime, dt) :
        # self.trans.x = NOW_PIXEL - gametime*RATE
        self.trans.x = -gametime*RATE + NOW_PIXEL

