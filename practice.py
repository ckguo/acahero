#pset6.py

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
from song_data import SongData
from settings import getAudioFiles, getDisplayFiles

Config.set('graphics', 'fullscreen', 'auto')
Config.write()

SCREEN_TIME = 3.0 # Amount of time 
RATE = Window.width/SCREEN_TIME

class MainWidgetPractice(BaseWidget) :
	def __init__(self, song, part, **kwargs):
		super(MainWidgetPractice, self).__init__(**kwargs)
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

		self.next_phrase_label = center_label()
		self.add_widget(self.next_phrase_label)

		self.clock = Clock()
		self.clock.stop()
		self.gametime = -SCREEN_TIME
		self.gameon = False

		self.old_cursor_y = 1
		self.filter_rate = 0.4

		# Display user's cursor
		self.cursorcol = Color(.6,.6,.6)
		self.canvas.add(self.cursorcol)
		self.user = Triangle(points=[NOW_PIXEL-60, -30, NOW_PIXEL-60, 30, NOW_PIXEL, 0])
		self.canvas.add(self.user)

		# # Add particle system, which is used in BeatMatchDisplay when user sings the correct pitch.
		self.ps = ParticleSystem('particle/particle.pex')
		self.add_widget(self.ps)

		# Display screen when starting game. 
		# self.name.text = "[color=000000][b]ACAHERO[/b]"
		self.scorelabel.text = "[color=000000]Score: 0"
		self.timelabel.text = "Time: %.2f" % self.gametime
		# self.streaklabel.text = "[color=000000][b]keys[/b]\n[i]p:[/i] [size=30]play | pause[/size]"
		
		self.gems_txt, self.barlines_txt, self.beats_txt = getDisplayFiles(song, part)

		song_data = SongData()
		song_data.read_data(self.gems_txt, self.barlines_txt, self.beats_txt)
		self.lanes = song_data.lanes

		self.phrases = create_phrase_song_data(song_data)
		self.phrase_num = 0
		self.passing = True

		current_phrase = self.phrases[self.phrase_num]
		self.end_time = current_phrase.end_time

		self.healthbar = HealthBar()
		self.progress = ProgressBar(len(self.phrases))
		self.display = BeatMatchDisplay(self.phrases[0], self.ps, RATE)
		self.canvas.add(self.healthbar)
		self.canvas.add(self.progress)
		self.canvas.add(self.display)

		self.bg_filename, self.part_filename = getAudioFiles(song, part)
		self.audio = PhraseAudioController(self.bg_filename, self.part_filename, self.receive_audio, current_phrase.start_time, current_phrase.phrase_length)

		self.player = PhrasePlayer(self.phrases[0], self.display, self.audio, PitchDetector())

		self.display.draw_objects()

	def toggle(self):
		self.gameon = not self.gameon
		self.audio.toggle()
		self.display.toggle()
		self.clock.toggle()
		Window.clearcolor = (1, 1, 1, 1) if self.gameon else (.8,.8,.8,.8)

	def endgame(self):
		self.toggle()
		self.timelabel.text = "Game Ended"
		if self.passing:
			self.streaklabel.text = 'Congrats! You passed Practice Mode!'
		else:
			self.streaklabel.text = 'Good job on completing Practice Mode!\nPlease try again until you pass every phrase.'

	def get_cursor_y(self):
		if self.player.cur_pitch == 0:
			return None
		bottom_pitch = self.lanes[-2] - 12
		top_pitch = self.lanes[1] + 12
		if self.player.cur_pitch < bottom_pitch:
			return 0
		if self.player.cur_pitch >= top_pitch:
			return GAME_HEIGHT
		bottom_i = -1
		top_i = len(self.lanes)
		# find the two lanes that the pitch is between
		for i in range(len(self.lanes)):
			if self.player.cur_pitch < self.lanes[i]:
				top_i = i
				top_pitch = self.lanes[i]
				break
			else:
				bottom_i = i
				bottom_pitch = self.lanes[i]
		# snap to the nearest 1/3
		frac = round((self.player.cur_pitch-bottom_pitch)/(top_pitch-bottom_pitch)*5)/5.
		bottom_pos = lane_to_y_pos(bottom_i, len(self.lanes))
		top_pos = lane_to_y_pos(top_i, len(self.lanes))
		# return the y position that the cursor should be at
		return bottom_pos + frac*(top_pos-bottom_pos)

	def goto_next_phrase(self):
		self.progress.add_phrase_bar(self.player.get_score())
		self.clock = Clock()
		self.phrase_num += 1
		if self.phrase_num == len(self.phrases):
			self.endgame()
			return
		phrase_data = self.phrases[self.phrase_num]

		self.canvas.remove(self.display)
		self.display = BeatMatchDisplay(phrase_data, self.ps, RATE)
		self.canvas.add(self.display)

		self.audio.toggle()
		self.audio = PhraseAudioController(self.bg_filename, self.part_filename, self.receive_audio, phrase_data.start_time, phrase_data.phrase_length)

		self.player = PhrasePlayer(phrase_data, self.display, self.audio, PitchDetector())
		self.display.draw_objects()
		self.audio.toggle()
		self.toggle()


	def on_update(self) :
		# Only update when gameplay is on
		if self.gameon:
			curr_gametime = self.clock.get_time() - SCREEN_TIME
			self.gametime = curr_gametime

			self.timelabel.text = "Time: %.2f" % self.gametime
			self.scorelabel.text = 'Score: {:4.2f}'.format(self.player.get_score())

			# Only display a streak if there is a current streak > 1
			self.streaklabel.text = ''
			self.next_phrase_label.text = ''

			flag = self.player.on_update(self.gametime)

			if flag == False or flag == True:
				if flag == False:
					self.passing = False
				self.goto_next_phrase()
				if self.phrase_num == len(self.phrases):
					return
				if flag == True:
					self.next_phrase_label.text = "Congratulations!\nHere's the next phrase :)"
				else:
					self.next_phrase_label.text = "Try again later!\nHere's the next phrase :)"

			self.healthbar.on_update(self.player.get_score())

			# 3,2,1 Start game countdown
			if -3 < self.gametime < -2:
				self.streaklabel.text = '3'
			elif -2 < self.gametime < -1:
				self.streaklabel.text = '2'
			elif -1 < self.gametime < 0:
				self.streaklabel.text = '1'

			# End game
			if self.gametime > self.end_time+2:
				self.endgame()
		
		if self.player.cur_pitch == 0:
			self.cursorcol.r = 0.6
			self.cursorcol.g = 0.6
			self.cursorcol.b = 0.6
		else:
			self.cursorcol.r = 0
			self.cursorcol.g = 0
			self.cursorcol.b = 0

		y = self.get_cursor_y()
		if y == None:
			return
		# Update the user's cursor
		if y < GAME_HEIGHT:
			cursor_y = self.filter_rate*y + (1-self.filter_rate)*self.old_cursor_y
			self.old_cursor_y = cursor_y
			self.user.points = [NOW_PIXEL-60, cursor_y-30, NOW_PIXEL-60, cursor_y+30, NOW_PIXEL, cursor_y]

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
class PhraseAudioController(object):
	def __init__(self, bg_path, solo_path, receive_audio_func, start_time, duration):
		super(PhraseAudioController, self).__init__()
		self.audio = Audio(2, input_func=receive_audio_func)
		self.mixer = Mixer()
		self.audio.set_generator(self.mixer)

		fs = 44100

		bg_wave_buffer = WaveBuffer(bg_path, int(start_time*fs), int(duration*fs))
		solo_wave_buffer = WaveBuffer(solo_path, int(start_time*fs), int(duration*fs))

		self.wave_gen_bg = WaveGenerator(bg_wave_buffer, loop=True)
		self.wave_gen_solo = WaveGenerator(solo_wave_buffer, loop=True)
		self.wave_gen_bg.pause()
		self.wave_gen_solo.pause()

	def start_music(self):
		self.wave_gen_solo.set_gain(0.8)
		self.wave_gen_bg.set_gain(0.7)

		self.mixer.add(self.wave_gen_solo)
		self.mixer.add(self.wave_gen_bg)

	# start / stop the song
	def toggle(self):
		self.wave_gen_bg.play_toggle()
		self.wave_gen_solo.play_toggle()

	# needed to update audio
	def on_update(self, gametime):
		self.audio.on_update()

		if gametime >= 0.:
			self.start_music()

def create_phrase_song_data(song_data):
	phrases = []
	barlines = song_data.barline_data
	beat_ind = 0
	gem_ind = [0]*len(song_data.lanes)
	start_time = 0
	# phrase_times = barlines[::4]

	for i in range(4, len(barlines), 4):
		end_time = barlines[i]

		for j in range(beat_ind, len(song_data.beat_data)):
			if song_data.beat_data[j] > end_time:
				break
		phrase_beats = song_data.beat_data[beat_ind:j]
		beat_ind = j

		phrase_gems = {}
		for lane in range(len(song_data.lanes)):
			for j in range(gem_ind[lane], len(song_data.gem_data[lane])):
				if song_data.gem_data[lane][j][0] >= end_time:
					break
			phrase_gems[lane] = song_data.gem_data[lane][gem_ind[lane]:j]
			gem_ind[lane] = j

		phrase_barlines = barlines[i-4:i+1]

		phrase_data = PhraseSongData(song_data.lanes, phrase_barlines, phrase_beats, phrase_gems)
		phrases.append(phrase_data)
		start_time = end_time

	return phrases

class PhraseSongData(object):
	def __init__(self, lanes, barlines, beats, gems):
		self.lanes = lanes
		self.phrase_length = barlines[-1] - barlines[0]

		num_repeats = 2
		self.end_time = num_repeats*self.phrase_length
		self.start_time = barlines[0]

		self.barline_data = []
		self.beat_data = []
		self.gem_data = {}

		for i in range(num_repeats):
			for lane in range(len(self.lanes)):
				lane_gems = []
				for gem in gems[lane]:
					lane_gems.append((gem[0]-self.start_time+i*self.phrase_length, gem[1], gem[2]))
				self.gem_data.setdefault(int(lane), []).extend(lane_gems)
			for bar in barlines:
				self.barline_data.append(bar-self.start_time+i*self.phrase_length)
			for beat in beats:
				self.beat_data.append(beat-self.start_time+i*self.phrase_length)

# Handles game logic and keeps score.
# Controls the display and the audio
class PhrasePlayer(object):
	def __init__(self, phrase_song_data, display, audio_ctrl, pitch_detector):
		super(PhrasePlayer, self).__init__()
		self.phrase_song_data = phrase_song_data
		self.phrase_length = phrase_song_data.phrase_length

		self.lanes = phrase_song_data.lanes
		self.num_lanes = len(self.lanes)
		self.display = display
		self.audio = audio_ctrl

		self.slop_window = 0.1
		self.gem_data = phrase_song_data.gem_data
		self.gem_idx = [0]*self.num_lanes
		self.gem_status = [[False]*len(self.gem_data[lane]) for lane in self.gem_data]
		self.score = 10
		self.max_score = 10
		self.should_reset_score = False

		self.gem_threshold = 0.25

		self.pitch = pitch_detector
		self.correct_pitch = 0
		self.cur_pitch = 0
		self.cor_lane = 0
		self.cur_gem = False # Tuple (lane, gem_idx)

		self.time = 0
		self.passed = False
		self.score_threshold = 0.6

	def get_score(self):
		return min(self.score/self.max_score, 1.0)

	def reset_score(self):
		self.score = 10
		self.max_score = 10

	def on_update(self, gametime):
		self.time = gametime

		# return False if gametime is too long
		if gametime > self.phrase_song_data.end_time + 0.5:
			return False

		time_in_phrase = self.time % self.phrase_length

		# if you are near the beginning of a phrase, return True if you had passed the phrase
		# reset the score at the start of a phrase
		if time_in_phrase < 0.1:
			if self.passed:
				return True
			if gametime > self.phrase_song_data.end_time:
				return False
			self.reset_score()
			self.should_reset_score = False

		# if you are near the end of the phrase, evaluate whether or not you passed the phrase
		if self.phrase_length - time_in_phrase < 0.05 and self.time > 0:
			self.should_reset_score = True
			if self.get_score() > self.score_threshold:
				self.passed = True

		self.audio.on_update(self.time)
		self.display.on_update(self.time)

		# find the current gem (if there is one) and set self.correct_pitch
		for lane in range(self.num_lanes):
			gem_idx = self.gem_idx[lane]

			if lane in self.gem_data and gem_idx < len(self.gem_data[lane]):
				gem_time, duration, lyric = self.gem_data[lane][gem_idx]

				if gem_time < gametime < gem_time + duration:
					self.correct_pitch = self.lanes[lane]
					self.cur_gem = (lane, gem_idx)

				if gametime > gem_time + duration:
					self.correct_pitch = 0
					self.cur_gem = False
					self.gem_idx[lane] += 1
					self.max_score += 2
		# return True

	def receive_audio(self, mono):
		if self.correct_pitch in self.lanes:
			self.cor_lane = self.lanes.index(self.correct_pitch)
		else:
			self.cor_lane = -1

		if self.cur_pitch != 0:
			conf = 0.5
		else:
			conf = 0.8
		self.cur_pitch = self.pitch.write(mono, conf)
		fs = 44100.

		if np.round(self.cur_pitch) == self.correct_pitch:
			# if you're correctly silent, smaller multiplier for score increase
			if np.round(self.cur_pitch) == 0:
				action = 'silent'
				self.score += 0.1*len(mono)/fs

			# if you're correctly singing a note, larger multiplier for score increase
			else:
				action = 'on'
				self.score += 5*len(mono)/fs
				# This is the bonus for hitting each note
				if not self.gem_status[self.cor_lane][self.gem_idx[self.cor_lane]]:
					self.score += 2
					self.gem_status[self.cor_lane][self.gem_idx[self.cor_lane]] = True
		
		# If you're singing when you're supposed to be silent 
		elif self.correct_pitch == 0:
			action = 'miss'
			self.score -= 0.1*len(mono)/fs

		# If you're silent when supposed to be singing, small penalty
		elif self.cur_pitch == 0:
			action = 'pass'
			self.score -= 0.1*len(mono)/fs

		# If you're singing the wrong note, you're penalized more based on how far off you are
		else:
			action = 'off'
			self.score -= 0.5*len(mono) * max(2,(np.round(self.cur_pitch) - self.correct_pitch))/fs

		# max score is just used for the percent calculation, don't worry about it
		self.score = max(0, self.score)
		if self.correct_pitch != 0: 
			self.max_score += 3*len(mono)/fs
		else:
			self.max_score += 0.1*len(mono)/fs

		self.display.animate_action(action, self.cur_gem)

if __name__ == '__main__': 
	run(MainWidgetPractice)
