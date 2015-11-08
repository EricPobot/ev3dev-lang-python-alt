#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        self.ev3_buttons = ev3.Buttons()
        self.ev3_buttons.on_change = self.on_change
        self.ev3_buttons.on_back = self.on_back

    def _display_button_state(self, name, pressed):
        y, x = self.btn_pos[name]
        self.stdscr.addstr(y, x, '[X]' if pressed else '[ ]')

    def on_change(self, buttons):
        dirty = False
        for btn, state in buttons:
            self._display_button_state(btn, state)
            dirty = True

        if dirty:
            self.stdscr.refresh()

    def on_back(self, state):
        self._display_button_state(ev3.Buttons.BACK, state)
        self.stdscr.refresh()

        self.done = True

    def run(self):
        self.stdscr = curses.initscr()
        height, width = self.stdscr.getmaxyx()
        # if width > 21:
        #     for name, yx in self.btn_pos.iteritems():
        #         self.btn_pos[name] = [2 * n for n in yx]
        curses.curs_set(0)

        for i, s in enumerate(['Press brick buttons', '(BACK to exit)']):
            self.stdscr.addstr(i + 1, 0, s.center(width))

        for name in self.btn_pos.iterkeys():
            self._display_button_state(name, False)

        self.stdscr.refresh()

        try:
            while not self.done:
                self.ev3_buttons.process()
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

        self.stdscr.addstr(height - 1, 0, '** demo ending **'.center(width - 1))
        self.stdscr.refresh()
        time.sleep(3)

        curses.curs_set(1)
        curses.endwin()


if __name__ == '__main__':
    Demo().run()
