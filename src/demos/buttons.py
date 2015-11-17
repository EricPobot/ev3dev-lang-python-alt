#!/usr/bin/env python
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

""" This demo displays the state of the EV3 brick buttons on its LCD.

It illustrates how to attach handlers to the slots defined for
individual buttons and for the global state change.

It also shows a simple use of curses to place text at arbitrary locations
on the LCD.
"""

import time
import curses

from ev3dev import ev3


class Demo(object):
    done = False
    stdscr = None

    btn_pos = {
        'up': (6, 9),
        'down': (12, 9),
        'left': (9, 5),
        'right': (9, 13),
        'enter': (9, 9),
        'back': (5, 3),
    }

    def __init__(self):
        # get an instance of the EV3 buttons manager
        self.ev3_buttons = ev3.Buttons()

        # attach handlers to the signals of interest
        self.ev3_buttons.on_change = self.on_change
        self.ev3_buttons.on_back = self.on_back

    def _display_button_state(self, name, pressed):
        """ Displays the state of a button on the LCD.

        The display location is defined by the class attribute `btn_pos`.

        Args:
            name (str): the name of the button
            pressed (bool): is it pressed or not
        """
        y, x = self.btn_pos[name]
        self.stdscr.addstr(y, x, '[X]' if pressed else '[ ]')

    def on_change(self, buttons):
        """ Displays the state off all the buttons which state has
        changed since last time.

        Args:
            buttons (list[tuple[str, bool]]): the list of changed button states
        """
        dirty = False

        # show the new state of buttons which have changed
        for btn, state in buttons:
            self._display_button_state(btn, state)
            dirty = True

        # if we wrote something, it's time to update the display
        if dirty:
            self.stdscr.refresh()

    def on_back(self, state):
        """ Handle the BACK button state change.

        We display it and set the demo termination flag.

        Args:
            state (bool): the new state
        """
        self._display_button_state(ev3.Buttons.BACK, state)
        self.stdscr.refresh()

        self.done = True

    def run(self):
        """ Runs the demo.
        """
        self.stdscr = curses.initscr()
        height, width = self.stdscr.getmaxyx()
        # if width > 21:
        #     for name, yx in self.btn_pos.iteritems():
        #         self.btn_pos[name] = [2 * n for n in yx]
        curses.curs_set(0)

        # displays a header
        for i, s in enumerate(['Press brick buttons', '(BACK to exit)']):
            self.stdscr.addstr(i + 1, 0, s.center(width))

        # initializes the screen by displaying the current button states
        for name in self.btn_pos.iterkeys():
            self._display_button_state(name, False)

        self.stdscr.refresh()

        try:
            # get button states and process them until the termination flag is set
            while not self.done:
                self.ev3_buttons.process()
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

        # gently say goodbye
        self.stdscr.addstr(height - 1, 0, '** demo ending **'.center(width - 1))
        self.stdscr.refresh()
        time.sleep(3)

        # final curses housekeeping
        curses.curs_set(1)
        curses.endwin()


if __name__ == '__main__':
    Demo().run()
