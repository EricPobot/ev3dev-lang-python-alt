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

import time
from textwrap import wrap

from ev3dev import ev3

print(wrap("Runs motors connected to outputs B and C in sync", 20))

motors = [ev3.LargeMotor(p) for p in ('outB', 'outC')]

# configure the motors
for m in motors:
    m.reset()
    m.duty_cycle_sp = 100
    m.stop_command = ev3.LargeMotor.STOP_COMMAND_BRAKE
    m.ramp_up_sp = 500
    m.ramp_down_sp = 500

print("2 turns forward :")
for m in motors:
    m.run_to_rel_pos(position_sp=360 * 2)

print('+ waiting for end...')
while m.state and 'holding' not in m.state:
    time.sleep(0.1)
print('+ complete.')

time.sleep(0.5)

print('backwards now :')
for m in motors:
    m.run_to_rel_pos(position_sp=-360 * 2)

print('+ waiting for end...')
while m.state and 'holding' not in m.state:
    time.sleep(0.1)
print('+ complete.')

time.sleep(0.5)
for m in motors:
    m.reset()

print("That's all folks.")
time.sleep(5)
