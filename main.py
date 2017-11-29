from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from project import MainWidget
from practice import MainWidgetPractice


class MenuScreen(Screen):
    pass

class PracticeScreen(Screen):
    def __init__(self, **kwargs):
        super(PracticeScreen, self).__init__(**kwargs)
        self.widget = MainWidgetPractice()
        self.start = True 

    def startWidget(self):
        if self.start: 
            self.add_widget(self.widget)
            self.start = False

        self.widget.toggle()

class PerformScreen(Screen):
    def __init__(self, **kwargs):
        super(PerformScreen, self).__init__(**kwargs)
        self.widget = MainWidget()
        self.start = True 

    def startWidget(self):
        if self.start: 
            self.add_widget(self.widget)
            self.start = False
            
        self.widget.toggle()

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
