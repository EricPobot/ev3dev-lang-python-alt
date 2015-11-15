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

""" Pilot demonstration.
"""

import os
import time

from ev3dev import ev3

from ev3dev.navigation import DifferentialPilot

_HERE = os.path.dirname(__file__)

pilot = DifferentialPilot(
    wheel_diameter=43.2,
    track_width=140,
    left_motor=ev3.LargeMotor(port=ev3.OUTPUT_B),
    right_motor=ev3.LargeMotor(port=ev3.OUTPUT_C),
    motors_settings={
        'ramp_up_sp': 500
    }
)

pilot.travel_speed = 100
pilot.rotate_speed = 90

start_time = None


def started(monitor):
    global start_time
    start_time = time.time()
    print('> started')


def complete(monitor):
    print('> completed in %.1fs' % (time.time() - start_time))


def stalled(monitor):
    print('> ** stalled **')

mon = pilot.travel(distance=200, on_start=started, on_complete=complete, on_stalled=stalled)

print('waiting...')
mon.wait(5)

if mon.running:
    print('not enough time')
elif mon.stalled:
    print('obstacle found')
else:
    print('success')

pilot.travel(distance=-200, speed=50, on_start=started, on_complete=complete, on_stalled=stalled).wait(5)
print('back home')

print('forward forever')
pilot.forward()
time.sleep(1)
print('time to stop')
pilot.stop()

print('backward forever')
pilot.backward(speed=50)
time.sleep(2)
pilot.stop()

print('rotate 90L')
pilot.rotate_left(angle=90, on_start=started, on_complete=complete).wait(5)
print('rotate 90R')
pilot.rotate_right(angle=90, speed=45, on_start=started, on_complete=complete).wait(5)

print('arc left-fwd')
pilot.arc(140, 90).wait(5)
print('arc left-back')
pilot.arc(140, -90).wait(5)

print('null radius arcs')
pilot.arc(0, 90).wait(5)
pilot.arc(0, -90).wait(5)

time.sleep(3)
pilot.stop(stop_command=ev3.RegulatedMotor.STOP_COMMAND_COAST)
print("That's all folks")
