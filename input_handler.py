from pynput.keyboard import Listener, Key

class InputHandler:
    def __init__(self):
        self.inputs: list[Key] = []
        self.listener = Listener(
            on_press=self._onPress, on_release=self._onRelease
        ).start()

    def _onPress(self, key: Key):
        if key not in self.inputs:
            self.inputs.append(key)

    def _onRelease(self, key: Key):
        if key in self.inputs:
            self.inputs.remove(key)

