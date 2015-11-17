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

""" This demo illustrates how to use the two red-green LEDs of the EV3 brick.
"""

import time
import math

from ev3dev import ev3

leds = ev3.Leds()

leds.all_off()
time.sleep(1)

# cycle LEDs like a traffic light
for _ in xrange(3):
    for m in (leds.green_on, leds.amber_on, leds.red_on):
        m()
        time.sleep(0.5)

leds.all_off()
time.sleep(0.5)

# blink LEDs from side to side now
for _ in xrange(3):
    for led in (leds.red_left, leds.red_right, leds.green_left, leds.green_right):
        led.brightness_pct = 100
        time.sleep(0.5)
        led.brightness_pct = 0

leds.all_off()
time.sleep(0.5)

# continuous mix of colors
for i in xrange(360):
    rd = math.radians(10 * i)
    leds.red_left.brightness_pct = .5 * (1 + math.cos(rd))
    leds.green_left.brightness_pct = .5 * (1 + math.sin(rd))
    leds.red_right.brightness_pct = .5 * (1 + math.sin(rd))
    leds.green_right.brightness_pct = .5 * (1 + math.cos(rd))
    time.sleep(0.05)

leds.all_off()
time.sleep(0.5)
