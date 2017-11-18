from common.gfxutil import *

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from common.kivyparticle import ParticleSystem

import numpy as np

NOW_PIXEL = 60 # Pixel of now bar
SCREEN_TIME = 3.0 # Amount of time 
GAME_HEIGHT = Window.height - 100 # Top of game screen

# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color, length):
        super(GemDisplay, self).__init__()  
        self.color = color
        self.pos = (pos[0], pos[1]-5)
        self.length = length
        self.draw_gem()

    def draw_gem(self):
        self.add(self.color)
        self.gem = Rectangle( pos=self.pos, size=(self.length,10) )
        self.add(self.gem)

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
        self.lines = [Line(points=[(799, np.interp(y, [-1,self.num_lanes], [0,GAME_HEIGHT])), (0, np.interp(y, [-1,self.num_lanes], [0,GAME_HEIGHT]))], width=0.4) for y in range(self.num_lanes)]      
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
        for lane in range(5):
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