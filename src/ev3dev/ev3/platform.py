# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2015 Eric Pascual
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

""" An assortment of classes modeling specific features of the EV3 brick.
"""

from ..core import *

OUTPUT_A = 'outA'
OUTPUT_B = 'outB'
OUTPUT_C = 'outC'
OUTPUT_D = 'outD'

INPUT_1 = 'in1'
INPUT_2 = 'in2'
INPUT_3 = 'in3'
INPUT_4 = 'in4'


class Leds(object):
    """ The EV3 LEDs.

    The EV3 brick has two bi-color LEDs which can be addressed individually.
    """

    red_left = Led(name='ev3-left0:red:ev3dev')
    red_right = Led(name='ev3-right0:red:ev3dev')
    green_left = Led(name='ev3-left1:green:ev3dev')
    green_right = Led(name='ev3-right1:green:ev3dev')

    @staticmethod
    def mix_colors(red, green):
        Leds.red_left.brightness_pct = red
        Leds.red_right.brightness_pct = red
        Leds.green_left.brightness_pct = green
        Leds.green_right.brightness_pct = green

    @staticmethod
    def set_red(pct):
        Leds.mix_colors(red=1 * pct, green=0 * pct)

    @staticmethod
    def red_on():
        Leds.set_red(1)

    @staticmethod
    def set_green(pct):
        Leds.mix_colors(red=0 * pct, green=1 * pct)

    @staticmethod
    def green_on():
        Leds.set_green(1)

    @staticmethod
    def set_amber(pct):
        Leds.mix_colors(red=1 * pct, green=1 * pct)

    @staticmethod
    def amber_on():
        Leds.set_amber(1)

    @staticmethod
    def set_orange(pct):
        Leds.mix_colors(red=1 * pct, green=0.5 * pct)

    @staticmethod
    def orange_on():
        Leds.set_orange(1)

    @staticmethod
    def set_yellow(pct):
        Leds.mix_colors(red=0.5 * pct, green=1 * pct)

    @staticmethod
    def yellow_on():
        Leds.set_yellow(1)

    @staticmethod
    def all_off():
        Leds.red_left.brightness = 0
        Leds.red_right.brightness = 0
        Leds.green_left.brightness = 0
        Leds.green_right.brightness = 0


class Buttons(ButtonManagerEVIO):
    """ EV3 Buttons.

    This class defines the 6 EV3 buttons. Their default handlers are implemented as
    empty methods.

    It adds a property for each button returning its current state.
    """

    #: Identifier of the "BACK" button
    BACK = 'back'
    #: Identifier of the "UP" button
    UP = 'up'
    #: Identifier of the "DOWN" button
    DOWN = 'down'
    #: Identifier of the "LEFT" button
    LEFT = 'left'
    #: Identifier of the "RIGHT" button
    RIGHT = 'right'
    #: Identifier of the "ENTER" button
    ENTER = 'enter'


    @staticmethod
    def on_up(state):
        """ This handler is called by `process()` whenever state of 'UP' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    @staticmethod
    def on_down(state):
        """ This handler is called by `process()` whenever state of 'DOWN' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    @staticmethod
    def on_left(state):
        """
        This handler is called by `process()` whenever state of 'LEFT' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    @staticmethod
    def on_right(state):
        """
        This handler is called by `process()` whenever state of 'RIGHT' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    @staticmethod
    def on_enter(state):
        """
        This handler is called by `process()` whenever state of 'ENTER' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    @staticmethod
    def on_back(state):
        """
        This handler is called by `process()` whenever state of 'BACK' button
        has changed since last `process()` call.

        Args:
            state (str): the new state of the button.
        """
        pass

    _buttons = {
        UP: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 103),
        DOWN: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 108),
        LEFT: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 105),
        RIGHT: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 106),
        ENTER: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 28),
        BACK: ButtonDefinition('/dev/input/by-path/platform-gpio-keys.0-event', 14),
    }

    @property
    def up(self):
        """ UP button status

        :type: bool
        """
        return self.UP in self.buttons_pressed

    @property
    def down(self):
        """ DOWN button status

        :type: bool
        """
        return self.DOWN in self.buttons_pressed

    @property
    def left(self):
        """ LEFT button status

        :type: bool
        """
        return self.LEFT in self.buttons_pressed

    @property
    def right(self):
        """ RIGHT button status

        :type: bool
        """
        return self.RIGHT in self.buttons_pressed

    @property
    def enter(self):
        """ ENTER button status

        :type: bool
        """
        return self.ENTER in self.buttons_pressed

    @property
    def back(self):
        """ BACK button status

        :type: bool
        """
        return self.BACK in self.buttons_pressed
