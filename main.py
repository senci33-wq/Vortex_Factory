from kivy.app import App
from kivy.uix.button import Button
import webbrowser

class MainApp(App):
    def build(self):
        btn = Button(text='Augsburger Tafel (Sicherer Link)')
        # Wir erzwingen http, um den SSL-Fehler zu umgehen
        btn.bind(on_release=lambda x: webbrowser.open('http://www.augsburger-tafel.de'))
        return btn

MainApp().run()