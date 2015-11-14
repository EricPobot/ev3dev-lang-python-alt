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

""" A complete robot demonstration.

The Grabber collects Duplo sized brick found on its path and grabs them back on
specific locations depending on their color.

It is built as a simplified Gripp3r, without the torso and with wheels instead
of treads. In addition, the gripper is fixed does not not lift.
"""

import time
import math
import threading
import os

from ev3dev import ev3
from ev3dev.display import Screen, Image


_HERE = os.path.dirname(__file__)


class Grabber(object):
    WHEELS_DIST = 140           # mm
    WHEEL_DIAMETER = 43.2       # mm

    EXPLORATION_RANGE = 300     # mm
    DEPOSIT_DIST = 250          # mm

    def __init__(self):
        self._motor_left = ev3.LargeMotor(port='outB')
        self._motor_right = ev3.LargeMotor(port='outC')
        self._motors = (self._motor_left, self._motor_right)

        self._gripper = Gripper(ev3.MediumMotor(port='outA'))

        self._color_sensor = ev3.ColorSensor(port='in1')
        self._start_btn = ev3.TouchSensor(port='in2')

        self._buttons = ev3.Buttons()
        self._buttons.on_back = self._back_button_pressed

        self._screen = Screen()
        self._screen.hide_cursor()

        self._done = False

        self._dist_per_pulse = self.WHEEL_DIAMETER * math.pi / self._motors[0].count_per_rot
        self._spin_per_pulse = math.degrees(self._dist_per_pulse / self.WHEELS_DIST * 2)

    def _back_button_pressed(self, state):
        self._done = True

    def reset(self):
        for m in self._motors:
            m.reset()
            m.duty_cycle_sp = 100
            m.stop_command = ev3.LargeMotor.STOP_COMMAND_HOLD
            m.ramp_up_sp = 500
            m.ramp_down_sp = 500

        self._color_sensor.mode = ev3.ColorSensor.MODE_COL_COLOR
        ev3.Leds.all_off()

        self._done = False

    def display_centered_image(self, name):
        self._screen.clear()
        img = Image.open(os.path.join(os.path.dirname(__file__), 'img', name + '.png'))
        self._screen.img.paste(img, tuple((d1 - d0) / 2 for d1, d0 in zip(self._screen.shape, img.size)))
        self._screen.update()

    def run(self):
        self.reset()

        ev3.Leds.heartbeat(red=1, green=1)
        self.display_centered_image("smiley-o")
        ev3.Sound.speak("I am calibrating my gripper")

        self.display_centered_image("smiley-busy")
        self._gripper.calibrate()
        self._gripper.open()

        ev3.Sound.speak('I am ready')
        self._buttons.start_scanner()

        self._done = False
        try:
            while not self._done:
                self.display_centered_image("smiley-o")
                LedFeedback.k2000(red=1, green=1)
                ev3.Sound.speak('Press touch sensor to start')

                self.display_centered_image("smiley-asleep")
                while not (self._start_btn.is_pressed or self._done):
                    time.sleep(0.1)
                while self._start_btn.is_pressed and not self._done:
                    time.sleep(0.1)

                if not self._done:
                    self.display_centered_image("smiley-waiting")
                    LedFeedback.searching()
                    self.grab_a_brick()

        finally:
            self._buttons.stop_scanner()

        ev3.Leds.red_on()

        img = Image.open(os.path.join(os.path.dirname(__file__), 'img', 'terminator.png'))
        self._screen.clear()
        self._screen.img.paste(img, (0, 0))
        self._screen.update()

        ev3.Sound.speak("I'll be back")

    def grab_a_brick(self):
        # reset encoders
        for m in self._motors:
            m.position = 0

        brick_found = self.drive_until_brick_found(max_dist=self.EXPLORATION_RANGE)
        good_one = None         # we don't need to set it here, but it's cleaner

        if brick_found:
            brick_color = self.analyze_brick()
            try:
                self.display_centered_image("smiley-happy")
                good_one = True

                msg = "this is a %s brick" % {
                    ev3.ColorSensor.COLOR_GREEN: 'green',
                    ev3.ColorSensor.COLOR_RED: 'red',
                }[brick_color]
                ev3.Sound.speak(msg)

            except KeyError:
                self.display_centered_image("smiley-wtf")
                ev3.Sound.speak("I do not know this color")
                good_one = False

            LedFeedback.brick_color(brick_color)

        else:
            self.display_centered_image("smiley-sad")
            ev3.Sound.speak("There is no brick")
            brick_color = None  # we don't need to set it, but it's cleaner
            ev3.Leds.all_off()

        # go back home first in any case
        dist = self._motor_left.position * self._dist_per_pulse
        ev3.Sound.play(os.path.join(_HERE, 'snd', 'backing_alert.rsf'))
        self.drive(-dist)

        if brick_found:
            if good_one:
                turn_direction = {
                        ev3.ColorSensor.COLOR_GREEN: -1,
                        ev3.ColorSensor.COLOR_RED: 1,
                    }[brick_color]

                self.spin(turn_direction * 90)
                self.drive(self.DEPOSIT_DIST)
                self._gripper.open()
                self.drive(-self.DEPOSIT_DIST)
                self.spin(-turn_direction * 90)

            else:
                self._gripper.open()
                self.display_centered_image("smiley-o")
                ev3.Sound.speak("Please take the brick")

        else:
            # nothing special to do here
            pass

        ev3.Leds.all_off()

    def drive_for_ever(self, power_pct=100):
        for m in self._motors:
            m.run_forever(
                duty_cycle_sp=power_pct
            )

    def drive(self, dist_mm, power_pct=100):
        """ Travels straight by a given distance.

        :param dist_mm: the distance of the travel
        :param power_pct: percent of power
        """
        pulses = dist_mm / self._dist_per_pulse
        for m in self._motors:
            m.position_sp = pulses
            m.duty_cycle_sp = power_pct

        self.run_and_wait_for_completion(absolute=False)

    def run_and_wait_for_completion(self, absolute=True):
        for m in self._motors:
            m.command = m.COMMAND_RUN_TO_ABS_POS if absolute else m.COMMAND_RUN_TO_REL_POS
        while any((m.state and 'holding' not in m.state for m in self._motors)):
            time.sleep(0.1)

    def stop(self, brake=True):
        for m in self._motors:
            m.stop(stop_command='brake' if brake else 'coast')

    def drive_until_brick_found(self, max_dist=300, power_pct=100):
        m = self._motors[0]
        limit = m.position + max_dist / self._dist_per_pulse
        self.drive_for_ever(power_pct=power_pct)
        while m.position <= limit and not self._color_sensor.value():
            time.sleep(0.1)
        self.stop()
        return self._color_sensor.value()

    def spin(self, degrees, power_pct=100):
        """ Spins by a given amount of degrees.

        :param degrees: spin degrees (>0 = CCW)
        :param power_pct: percent of power
        """
        pulses = degrees / self._spin_per_pulse
        for i, m in enumerate(self._motors):
            m.duty_cycle_sp = power_pct
            m.position_sp = pulses * (1 if i else -1)

        self.run_and_wait_for_completion(absolute=False)

    def analyze_brick(self):
        # move forward a bit gently to place the brick well inside the gripper
        self.drive(dist_mm=50, power_pct=30)
        self._gripper.close()

        # leave some time to the sensor for updating its reading accurately
        time.sleep(0.2)

        return self._color_sensor.value()


class Gripper(object):
    def __init__(self, motor):
        self._motor = motor
        self._open_position = self._close_position = None

    def calibrate(self):
        # cache the instance to avoid repetitive member lookup in loops
        m = self._motor

        def run_until_stalled(dc):
            last_pos = m.position
            m.run_forever(duty_cycle_sp=dc)
            time.sleep(0.5)
            while m.position != last_pos:
                last_pos = m.position
                time.sleep(0.1)
            m.stop(stop_command='coast')

        m.reset()
        calibration_duty_cycle = 30

        # move until the opening limit
        run_until_stalled(-calibration_duty_cycle)
        # go back a bit to avoid stressing the mechanics too much
        m.run_to_rel_pos(position_sp=100)
        time.sleep(0.5)

        # remember this position as the opening set point
        m.reset()
        self._open_position = 0

        # do the same to find the closing position
        run_until_stalled(calibration_duty_cycle)
        m.run_to_rel_pos(position_sp=-100)
        time.sleep(0.5)

        # remember this position as the closing set point
        self._close_position = m.position

    def _actuate_gripper(self, open_it):
        if any(p is None for p in (self._open_position, self._close_position)):
            raise Exception('need to calibrate first')

        m = self._motor

        m.run_to_abs_pos(
            duty_cycle_sp=100,
            stop_command='brake',
            position_sp=self._open_position if open_it else self._close_position
        )
        # wait while the motor is moving
        while m.state:
            time.sleep(0.1)

    def open(self):
        self._actuate_gripper(open_it=True)

    def close(self):
        self._actuate_gripper(open_it=False)

    def deactivate(self):
        self._motor.stop(stop_command='coast')


class LedFeedback(object):
    @staticmethod
    def brick_color(color):
        ev3.Leds.all_off()
        try:
            mix = {
                ev3.ColorSensor.COLOR_GREEN: (0, 1),
                ev3.ColorSensor.COLOR_RED: (1, 0),
            }[color]
        except KeyError:
            mix = (1, 1)

        for l in ev3.Leds.ALL:
            l.trigger = ev3.Led.TRIGGER_HEARTBEAT
        ev3.Leds.mix_colors(*mix)

    @staticmethod
    def k2000(red, green):
        period = 0.5

        def start_k2000():
            ev3.Leds.mix_colors(red, green)
            for group in (ev3.Leds.LEFT, ev3.Leds.RIGHT):
                for l in group:
                    if red and l in ev3.Leds.RED:
                        l.trigger = ev3.Led.TRIGGER_TIMER
                    if green and l in ev3.Leds.GREEN:
                        l.trigger = ev3.Led.TRIGGER_TIMER

                time.sleep(period)

        threading.Thread(target=start_k2000).start()

    @staticmethod
    def searching():
        period = 0.5

        def start_k2000():
            ev3.Leds.all_off()
            ev3.Leds.red_left.trigger = ev3.Led.TRIGGER_TIMER
            time.sleep(period)
            ev3.Leds.green_right.trigger = ev3.Led.TRIGGER_TIMER

        threading.Thread(target=start_k2000).start()


    @staticmethod
    def warning():
        ev3.Leds.amber_on()
        ev3.Leds.blink()

if __name__ == '__main__':
    robot = Grabber()
    try:
        robot.run()
    except KeyboardInterrupt:
        pass
    finally:
        robot.reset()
