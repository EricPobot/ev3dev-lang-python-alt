#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import math

from ev3dev import ev3

leds = ev3.Leds()

leds.all_off()
time.sleep(1)

for _ in xrange(3):
    for m in (leds.green_on, leds.amber_on, leds.red_on):
        m()
        time.sleep(0.5)

leds.all_off()
time.sleep(0.5)

for _ in xrange(3):
    for led in (leds.red_left, leds.red_right, leds.green_left, leds.green_right):
        led.brightness_pct = 100
        time.sleep(0.5)
        led.brightness_pct = 0

leds.all_off()
time.sleep(0.5)

for i in xrange(360):
    rd = math.radians(10 * i)
    leds.red_left.brightness_pct = .5 * (1 + math.cos(rd))
    leds.green_left.brightness_pct = .5 * (1 + math.sin(rd))
    leds.red_right.brightness_pct = .5 * (1 + math.sin(rd))
    leds.green_right.brightness_pct = .5 * (1 + math.cos(rd))
    time.sleep(0.05)

leds.all_off()
time.sleep(0.5)
