from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_string("""
<MenuScreen>:
    BoxLayout:
    	orientation: 'vertical'
    	spacing: 30
    	padding: [50,50,50,50]

        Button:
            text: 'Practice Mode'
            on_press: 
            	root.manager.transition.direction = 'left'
            	root.manager.current = 'settings'
        Button:
            text: 'Play Mode'
            on_press: 
            	root.manager.transition.direction = 'left'
            	root.manager.current = 'settings'
        Button:
            text: 'Settings'

<SettingsScreen>:
    BoxLayout:
        Button:
            text: 'My settings button'
        Button:
            text: 'Back to menu'
            on_press: 
            	root.manager.transition.direction = 'right'
            	root.manager.current = 'menu'
""")

# Declare both screens
class MenuScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

# Create the screen manager
sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(SettingsScreen(name='settings'))

class TestApp(App):

    def build(self):
        return sm

if __name__ == '__main__':
    TestApp().run()