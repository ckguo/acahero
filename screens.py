from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from project import *


class MenuScreen(Screen):
    pass

class PracticeScreen(Screen):
    pass
    
class PerformScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class ScreenManagement(ScreenManager):
    pass

# Create the screen manager
presentation = Builder.load_file("screen_manager.kv")

class MainApp(App):
    
    def build(self):
        return presentation

if __name__ == "__main__":
    MainApp().run()
