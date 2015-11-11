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

    This class is not supposed to be instantiated since there is a single set of
    LEDs on the brick. All its attributes and methods are defined either as
    static or class level.
    """

    #: The red LED on the left side of the brick
    red_left = Led(name='ev3-left0:red:ev3dev')
    #: The red LED on the right side of the brick
    red_right = Led(name='ev3-right0:red:ev3dev')
    #: The green LED on the left side of the brick
    green_left = Led(name='ev3-left1:green:ev3dev')
    #: The green LED on the right side of the brick
    green_right = Led(name='ev3-right1:green:ev3dev')

    #: The group containing the red LEDs
    RED = (red_left, red_right)
    #: The group containing the green LEDs
    GREEN = (green_left, green_right)
    #: The group containing the left side LEDs
    LEFT = (red_left, green_left)
    #: The group containing the right side LEDs
    RIGHT = (red_right, green_right)
    #: The group containing all the LEDs
    ALL = RED + GREEN

    @staticmethod
    def set_attributes(group, **kwargs):
        """ Sets attributes for each LED in a group.

        Args:
            group (tuple): a tuple containing the LEDs to be set (ex: :py:setattr:`RED`)
            \**kwargs: the attributes and their values

        Example::

            >>> Leds.set(LEFT, brightness_pct=0.5, trigger='timer')
        """
        for led in group:
            for k in kwargs:
                setattr(led, k, kwargs[k])

    @classmethod
    def mix_colors(cls, red, green):
        """ Set the color of all LEDs from the red/green percents, as defined
        by :py:meth:`ev3dev.core.Led.brightness_pct`.

        Args:
            red (float): red level
            green (float): green level
        """
        for l in cls.RED:
            l.brightness_pct = red
        for l in cls.GREEN:
            l.brightness_pct = green

    @staticmethod
    def set_red(pct):
        """ Lights the LEDs in a shade of red.

        Args:
            pct (float): brightness percent
        """
        Leds.mix_colors(red=1 * pct, green=0 * pct)

    @staticmethod
    def red_on():
        """ Turns the LEDs in full red.
        """
        Leds.set_red(1)

    @staticmethod
    def set_green(pct):
        """ Lights the LEDs in a shade of green.

        Args:
            pct (float): brightness percent
        """
        Leds.mix_colors(red=0 * pct, green=1 * pct)

    @staticmethod
    def green_on():
        """ Turns the LEDs in full green.
        """
        Leds.set_green(1)

    @staticmethod
    def set_amber(pct):
        """ Lights the LEDs in a shade of amber (equal mix of red and green).

        Args:
            pct (float): brightness percent
        """
        Leds.mix_colors(red=1 * pct, green=1 * pct)

    @staticmethod
    def amber_on():
        """ Turns the LEDs in full amber.
        """
        Leds.set_amber(1)

    @staticmethod
    def set_orange(pct):
        """ Lights the LEDs in a shade of orange (red-ish mix of red and green).

        Args:
            pct (float): brightness percent
        """
        Leds.mix_colors(red=1 * pct, green=0.5 * pct)

    @staticmethod
    def orange_on():
        """ Turns the LEDs in full orange.
        """
        Leds.set_orange(1)

    @staticmethod
    def set_yellow(pct):
        """ Lights the LEDs in a shade of orange (green-ish mix of red and green).

        Args:
            pct (float): brightness percent
        """
        Leds.mix_colors(red=0.5 * pct, green=1 * pct)

    @staticmethod
    def yellow_on():
        """ Turns the LEDs in full yellow.
        """
        Leds.set_yellow(1)

    @classmethod
    def all_off(cls):
        """ Turns all LEDs off.
        """
        for l in cls.ALL:
            l.trigger = Led.TRIGGER_ON
            l.brightness = 0

    @classmethod
    def blink(cls, leds=ALL, on=500, off=500):
        cls.all_off()
        for l in leds:
            l.trigger = 'timer'
            # TODO make this work
            # l.delay_on = on
            # l.delay_off = off

    @classmethod
    def steady(cls):
        for l in cls.ALL:
            l.trigger = Led.TRIGGER_ON

    @classmethod
    def heartbeat(cls, red, green):
        cls.steady()
        for l in cls.ALL:
            l.trigger = Led.TRIGGER_HEARTBEAT
        cls.mix_colors(red, green)


class Buttons(ButtonManagerEVIO):
    """ EV3 Buttons.

    This class defines the 6 EV3 buttons, with a class level property for each one,
    giving its current state.

    It also provides slots for attaching event handlers to be invoked on state changes.
    There are two levels of handler:

        - global : called as soon as a change is detected, passing it the list of changes
        - per button : called when a change is detected for this button

    By default, handlers are no-op. To use them, you must attach your handlers by overriding
    the default ones.

    Examples:

        >>> def my_up_handler(state):
        >>>     ...
        >>>
        >>> btns = ev3dev.ev3.Buttons()
        >>> btns.on_up = my_up_handler
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
