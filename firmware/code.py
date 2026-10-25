import keypad
import random
import touchio
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.control_change import ControlChange
from microcontroller import pin

from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.keys import KC, Key
from kmk.kmk_keyboard import KMKKeyboard
from kmk.modules.encoder import EncoderHandler
from kmk.modules.midi import MidiKeys
from kmk.modules.potentiometer import PotentiometerHandler
from kmk.scanners import Scanner
from kmk.scanners.keypad import KeysScanner


class TouchScanner(Scanner):
    def __init__(self, pins):
        self.pads = [touchio.TouchIn(p) for p in pins]
        self.pressed = [False] * len(pins)

    @property
    def key_count(self):
        return len(self.pads)

    def scan_for_changes(self):
        for i, pad in enumerate(self.pads):
            touched = pad.value
            if touched != self.pressed[i]:
                self.pressed[i] = touched
                return keypad.Event(i + self.offset, touched)


keyboard = KMKKeyboard()
midi = MidiKeys()
media_keys = MediaKeys()

octave_shift = 0
scale = [60, 62, 64, 65, 67, 69, 71]


class NoteKey(Key):
    def __init__(self, note):
        self.note = note
        self.active_note = None

    def on_press(self, keyboard, coord_int=None):
        self.active_note = self.note + octave_shift * 12
        midi.send(NoteOn(self.active_note, 100))

    def on_release(self, keyboard, coord_int=None):
        if self.active_note is not None:
            midi.send(NoteOff(self.active_note, 0))
            self.active_note = None


class RandomNoteKey(Key):
    def __init__(self):
        self.active_note = None

    def on_press(self, keyboard, coord_int=None):
        self.active_note = random.choice(scale) + octave_shift * 12
        midi.send(NoteOn(self.active_note, 100))

    def on_release(self, keyboard, coord_int=None):
        if self.active_note is not None:
            midi.send(NoteOff(self.active_note, 0))
            self.active_note = None


class OctaveKey(Key):
    def __init__(self, amount):
        self.amount = amount

    def on_press(self, keyboard, coord_int=None):
        global octave_shift
        octave_shift = max(-2, min(2, octave_shift + self.amount))
        print("Octave:", octave_shift)
        print("Octaaf:", octave_shift)


keyboard.matrix = [
    # Touch pads 1-7 (keys 0-6)
    TouchScanner([pin.GPIO13, pin.GPIO12, pin.GPIO11, pin.GPIO10, pin.GPIO9, pin.GPIO8, pin.GPIO7]),
    # Switches left, middle, right (keys 7-9)
    KeysScanner([pin.GPIO4, pin.GPIO5, pin.GPIO6], value_when_pressed=False, pull=True),
    TouchScanner([pin.GPIO1, pin.GPIO2, pin.GPIO3, pin.GPIO4, pin.GPIO5, pin.GPIO6, pin.GPIO7]),
    KeysScanner([pin.GPIO44, pin.GPIO43, pin.GPIO13], value_when_pressed=False, pull=True),
]

keyboard.keymap = [[
    NoteKey(60), NoteKey(62), NoteKey(64), NoteKey(65),
    NoteKey(67), NoteKey(69), NoteKey(71),
    OctaveKey(-1), RandomNoteKey(), OctaveKey(1),
]]

encoder = EncoderHandler()
encoder.pins = ((pin.GPIO43, pin.GPIO44, None),)
encoder.pins = ((pin.GPIO8, pin.GPIO9, None),)
encoder.map = [((KC.VOLD, KC.VOLU, KC.NO),)]

sliders = PotentiometerHandler()
sliders.pins = (
    (pin.GPIO2, lambda state: midi.send(ControlChange(1, state.position))),
    (pin.GPIO1, lambda state: midi.send(ControlChange(7, state.position))),
    (pin.GPIO10, lambda state: midi.send(ControlChange(7, state.position))),
    (pin.GPIO11, lambda state: midi.send(ControlChange(1, state.position))),
)

keyboard.modules = [midi, encoder, sliders]
keyboard.extensions = [
    media_keys,
    RGB(pixel_pin=pin.GPIO3, num_pixels=3, val_default=80, animation_mode=AnimationModes.RAINBOW),
    RGB(pixel_pin=pin.GPIO12, num_pixels=3, val_default=80, animation_mode=AnimationModes.RAINBOW),
]

if __name__ == '__main__':
    keyboard.go()
