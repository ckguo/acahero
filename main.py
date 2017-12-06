import os

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from project import MainWidget
from practice import MainWidgetPractice

# songs = os.listdir('songs')
# parts = ['Soprano', 'Alto', 'Tenor', 'Bass']
currpart = None
currsong = None


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        pass

    def setPart(self, new_part):
        global currpart
        currpart = new_part

    def setSong(self, new_song):
        global currsong
        currsong = new_song

class FirstSettingsScreen(SettingsScreen):
    def __init__(self, **kwargs):
        super(FirstSettingsScreen, self).__init__(**kwargs)
        pass

class MenuScreen(Screen):
    def goPractice(self):
        new_screen = 'practice_{}_{}'.format(currsong, currpart)
        self.manager.current = new_screen

    def goPerform(self):
        new_screen = 'perform_{}_{}'.format(currsong, currpart)
        self.manager.current = new_screen

class PracticeScreen(Screen):
    def __init__(self, song, part, **kwargs):
        super(PracticeScreen, self).__init__(**kwargs)
        self.widget = MainWidgetPractice(song, part)
        self.start = True 
        
    def startWidget(self):
        if self.start: 
            self.add_widget(self.widget)
            self.start = False
        self.widget.toggle()

class PracticeScreen_wdik_soprano(PracticeScreen):
    def __init__(self, **kwargs):
        super(PracticeScreen_wdik_soprano, self).__init__('wdik', 'Soprano', **kwargs)

class PracticeScreen_wdik_alto(PracticeScreen):
    def __init__(self, **kwargs):
        super(PracticeScreen_wdik_alto, self).__init__('wdik', 'Alto', **kwargs)

class PracticeScreen_wdik_tenor(PracticeScreen):
    def __init__(self, **kwargs):
        super(PracticeScreen_wdik_tenor, self).__init__('wdik', 'Tenor', **kwargs)

class PracticeScreen_wdik_bass(PracticeScreen):
    def __init__(self, **kwargs):
        super(PracticeScreen_wdik_bass, self).__init__('wdik', 'Bass', **kwargs)

class PerformScreen(Screen):
    def __init__(self, song, part, **kwargs):
        super(PerformScreen, self).__init__(**kwargs)
        self.widget = MainWidget(song, part)
        self.start = True 
        
    def startWidget(self):
        if self.start: 
            self.add_widget(self.widget)
            self.start = False
        self.widget.toggle()

class PerformScreen_wdik_soprano(PerformScreen):
    def __init__(self, **kwargs):
        super(PerformScreen_wdik_soprano, self).__init__('wdik', 'Soprano', **kwargs)

class PerformScreen_wdik_alto(PerformScreen):
    def __init__(self, **kwargs):
        super(PerformScreen_wdik_alto, self).__init__('wdik', 'Alto', **kwargs)

class PerformScreen_wdik_tenor(PerformScreen):
    def __init__(self, **kwargs):
        super(PerformScreen_wdik_tenor, self).__init__('wdik', 'Tenor', **kwargs)

class PerformScreen_wdik_bass(PerformScreen):
    def __init__(self, **kwargs):
        super(PerformScreen_wdik_bass, self).__init__('wdik', 'Bass', **kwargs)

class ScreenManagement(ScreenManager):
    pass

# Create the screen manager
presentation = Builder.load_file("screen_manager.kv")

class MainApp(App):
    
    def build(self):
        return presentation

if __name__ == "__main__":
    MainApp().run()
