import random
import threading
import Queue
from time import sleep
import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)

RED = 22
GREEN = 17
BLUE = 24
WHITE = 27

FREQ = 1000

gpio.setup([RED, GREEN, BLUE, WHITE], gpio.OUT)

class Color(gpio.PWM, object):
    def __init__(self, pin, freq=FREQ, brightness=0):
        self.as_super = super(Color, self) #hack in order for IPython to reload module correctly
        self.as_super.__init__(pin, freq)
        self.pin = pin
        self.freq = freq
        self.duty = 100
        self.brightness = brightness
        self.as_super.start(self.duty)
    
    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, b):
        b = 0 if b < 0 else b
        b = 255 if b > 255 else b
        self._brightness = b
        self.duty = (b/25.5)**2.0
        self.ChangeDutyCycle(self.duty)


class CompositeColor(object):
    def __init__(self, **kwargs):
        self.red = Color(RED, brightness=kwargs.get('red', 0))
        self.green = Color(GREEN, brightness=kwargs.get('green', 0))
        self.blue = Color(BLUE, brightness=kwargs.get('blue', 0))
        self.white = Color(WHITE, brightness=kwargs.get('white', 0))

        self.rgbw = kwargs.get('rgbw', '00000000')

    @property
    def rgbw(self):
        return self._rgbw

    @rgbw.setter
    def rgbw(self, vals):
        colors = [self.red, self.green, self.blue, self.white]
        if type(vals) != list:
            vals = breakout_rgbw(vals)
        self._rgbw = vals
        for color, val in zip(colors, vals):
            color.brightness = val

    def random(self):
        self.rgbw = '%08x' % random.randrange(16**8)

    def off(self):
        self.rgbw = '00000000'


class Pattern(object):
    def __init__(self, **kwargs):
        self.color = CompositeColor()

    def fade(self, start, end, bpm, length=1):
        # ff33dd44 --> aa99ee00
        start = breakout_rgbw(start)
        end = breakout_rgbw(end)
        # [255, 51, 221, 68] --> [170, 153, 238, 0]
        for i in range(0, bpm):
            self.color.rgbw = [a + i*(b-a)/bpm for a, b in zip(start, end)]
            sleep(60.0*length/(bpm**2))

    def random(self, bpm):
        self.color.random()
        sleep(60.0/bpm)


class Sequencer(threading.Thread):
    def __init__(self, **kwargs):
        self.as_super = super(Sequencer, self)
        self.as_super.__init__()
        self.stoprequest = threading.Event()
        self.pattern = kwargs.get('pattern', Pattern().random)
        self.bpm = float(kwargs.get('bpm', 120))

    def run(self):
        while not self.stoprequest.isSet():
            self.pattern(self.bpm)

    def join(self, timeout=None):
        self.stoprequest.set()
        self.as_super.join(timeout)


def breakout_rgbw(vals):
    if vals.startswith('0x'):
        vals = vals.strip('0x')
    vals = vals.zfill(8)
    vals = [int(vals[i:i+2], 16) for i in range(0, 8, 2)]
    return vals


def reset():
    red = Color(RED, FREQ, brightness=0)
    green = Color(GREEN, FREQ, brightness=0)
    blue = Color(BLUE, FREQ, brightness=0)
    white = Color(WHITE, FREQ, brightness=0)
    red.stop()
    green.stop()
    blue.stop()
    white.stop()


def display():
    t = 0.001

    red = Color(RED, FREQ)
    green = Color(GREEN, FREQ)
    blue = Color(BLUE, FREQ)
    white = Color(WHITE, FREQ)

    for c in [red, green, blue, white]:
        for i in range(0, 255):
            c.brightness = i
            sleep(t)

        for i in reversed(range(0, 255)):
            c.brightness = i
            sleep(t)



