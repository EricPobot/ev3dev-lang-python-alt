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

""" This modules provides the implementation of the concept of *pilots*, which are
high level entities intended to control the motion of a robot in a uniform way,
not depending on its mechanical architecture.

This encompasses the common differential architecture, but also the holonom, steering,...

This code is heavily based on LeJOS (http:www.lejos.org) one, its documentation being
reproduced as is when relevant, so that LeJOS users can quickly be productive.
"""

import math
import threading
import time

from .motors import RegulatedMotor


class BasePilot(object):
    """ Abstract base class for all kinds of pilots.
    """


class DifferentialPilot(BasePilot):
    """ The DifferentialPilot class is a software abstraction of the Pilot mechanism of a robot.
    It contains methods to control robot movements: travel forward or backward in a straight line
    or a circular path or rotate to a new direction.

    This class will only work with two independently controlled motors to steer differentially,
    so it can rotate within its own footprint (i.e. turn on one spot).

    In all the methods that cause the robot to change its heading (the angle relative
    to the X axis in which the robot is facing) the angle parameter specifies the change
    in heading. A positive angle causes a turn to the left (anti-clockwise) to increase the heading,
    and a negative angle causes a turn to the right (clockwise).
    """
    _travel_speed = 0
    _rotate_speed = 0

    def __init__(self, wheel_diameter, track_width, left_motor, right_motor, reverse=False, motors_settings=None):
        """
        Args:
            wheel_diameter (float): the diameter of the wheels
            track_width (float): the distance between wheel contact points on the ground
            left_motor (RegulatedMotor): the left motor
            right_motor (RegulatedMotor): the right motor
            reverse (bool): if true, the NXT robot moves forward when the motors are running backward
            motors_settings (dict): optional dictionary with motor settings

        Raise:
            ValueError: if any of the mandatory parameter is missing

        .. note::

            The dimensions units (wheel diameter, track with) can be anything (mm or cm) as long
            as all the properties use the same one.
        """
        if not all((wheel_diameter, track_width, left_motor, right_motor)):
            raise ValueError('all arguments are mandatory')

        self._wheel_diam = wheel_diameter
        self._track_width = track_width
        self._left_motor, self._right_motor = self._motors = (left_motor, right_motor)
        self._reverse = reverse

        self._dist_per_pulse = self._wheel_diam * math.pi / self._left_motor.count_per_rot
        self._rotation_per_pulse = math.degrees(self._dist_per_pulse / self._track_width * 2)

        self.reset_motors()

        # configure the motors, using reasonable settings for not specified ones
        settings = {
            'duty_cycle_sp': 100,
            'speed_regulation': RegulatedMotor.SPEED_REGULATION_ON,
            'stop_command': RegulatedMotor.STOP_COMMAND_HOLD,
            'ramp_up_sp': 500,
            'ramp_down_sp': 500
        }
        if motors_settings:
            settings.update(motors_settings)
        self.setup_motors(**settings)

    def reset_motors(self):
        """ Resets the motors
        """
        for m in self._motors:
            m.reset()

    def setup_motors(self, **kwargs):
        """ Configure the motors.

        Args:
            \**kwargs: the keyword arguments providing the desired attribute settings
        """
        for attr, value in kwargs.iteritems():
            for m in self._motors:
                setattr(m, attr, value)

    def _pulses_per_sec_linear(self, speed):
        """ Returns the number of pulses per second corresponding to the given linear speed.

        Args:
            speed (float): the speed in wheel diameter units per second

        Returns:
            int: the equivalent pulses per second
        """
        return round(speed / self._dist_per_pulse)

    def _pulses_per_sec_angular(self, speed):
        """ Returns the number of pulses per second corresponding to the given rotational peed.

        Args:
            speed (float): the speed in degrees per second

        Returns:
            int: the equivalent pulses per second
        """
        return round(speed / self._rotation_per_pulse)

    @property
    def travel_speed(self):
        """ The default robot travel speed, in wheel diameter units per second.

        .. note::

            The sign of the speed value is discarded. The direction can be controlled
            either by overriding the default value when calling :py:meth:`drive` or
            using methods :py:meth:`forward` and :py:meth:`backward`.

        :type: float
        """
        return self._travel_speed

    @travel_speed.setter
    def travel_speed(self, speed):
        self._travel_speed = abs(speed)

    @property
    def rotate_speed(self):
        """ The robot rotation speed, in degrees per second.

        .. note::

            The sign of the speed value is discarded. The direction can be controlled
            either by overriding the default value when calling :py:meth:`rotate` or
            using methods :py:meth:`rotate_right` and :py:meth:`rotate_left`.

        :type: float
        """
        return self._rotate_speed

    @rotate_speed.setter
    def rotate_speed(self, speed):
        self._rotate_speed = abs(speed)

    def drive(self, speed=None):
        """ Travels straight, at the speed previously set using :py:attr:`travel_speed`
        or locally overridden by the `speed` argument.

        Moves forward if speed is positive, backwards otherwise.

        Args:
            speed (float): optional speed
        """
        pulses_per_sec = self._pulses_per_sec_linear(speed or self._travel_speed)
        for m in self._motors:
            m.speed_regulation_enabled = m.SPEED_REGULATION_ON
            m.speed_sp = pulses_per_sec

        self._motors_sync_start()

    def forward(self, speed=None):
        """ Travels forward, no matter is the speed sign.
        """
        self.drive(abs(speed or self._travel_speed))

    def backward(self, speed=None):
        """ Travels backward, no matter is the speed sign.
        """
        self.drive(-abs(speed or self._travel_speed))

    def stop(self, stop_command=None):
        """ Immediate stop, using the current motor stop setting.

        Args:
            stop_command (str): optional stop command, among `RegulatedMotor.STOP_COMMAND_xxx`.
                If not provided, use the current motors setting
        """
        for m in self._motors:
            m.stop(stop_command=stop_command)

    def _motors_sync_start(self, command):
        """ Internal method used to start the motors in sync

        Args:
            command (str): the start command to be used (one of `COMMAND_RUN_xxx`)
        """
        for m in self._motors:
            m.command = command

    def travel(self, distance, speed=None, on_start=None, on_complete=None, on_stalled=None, callback_args=None):
        """ Travels for the specified distance at a given speed.

        This method is asynchronous, which means that it returns immediately. It returns
        the monitor created for tracking the motion.

        In addition, runnables can be passed, which will be called on various events
        (start of the move, end of the move, stalled detection).

        Example::

            >>> pilot = DifferentialPilot(43.2, 150, m_B, m_C)
            >>>
            >>> # synchronous usage with a forever wait
            >>> pilot.travel(250).wait(delay=None)
            >>>
            >>> # asynchronous usage
            >>> def arrived(pilot):
            >>>     print('just arrived')
            >>>
            >>> mvt = pilot.travel(distance=250, speed=100, on_complete=arrived)
            >>> # ... do something while traveling
            >>>
            >>> # wait at most 10 secs for arrival at destination before doing something else
            >>> mvt.wait(delay=10)
            >>> if mvt.not_done:
            >>>     print("something wrong happened while traveling")
            >>> else:
            >>>     print("we are at destination")

        Args:
            distance (float): the distance to be traveled, in wheel diameter unit
            speed (float): optional local override of the default speed as set by :py:attr:`travel_speed`
            on_start: optional callback for motion start event handling
            on_complete: optional callback for completion event handling
            on_stalled: optional callback for stalled detection handling
            callback_args (dict): optional dictionary defining the kwargs passed to the callbacks

        Returns:
            MotionMonitor: the motion monitoring object
        """
        pulses = round(distance / self._dist_per_pulse)
        pulses_per_sec = self._pulses_per_sec_linear(speed or self._travel_speed)

        for m in self._motors:
            m.position_sp = pulses
            m.speed_regulation_enabled = RegulatedMotor.SPEED_REGULATION_ON
            m.speed_sp = pulses_per_sec

        self._motors_sync_start(RegulatedMotor.COMMAND_RUN_TO_REL_POS)

        monitor = MotionMonitor(self,
                                on_start=on_start,
                                on_complete=on_complete,
                                on_stalled=on_stalled,
                                callback_args=callback_args
                                )
        monitor.start()

        return monitor

    def rotate(self, angle, speed=None, on_start=None, on_complete=None, on_stalled=None, callback_args=None):
        """ Rotates for the specified amount of degrees.

        Positive angles are counted CCW, negative ones CW. Callbacks mechanism is the same as for :py:meth:`travel`.

        Args:
            angle (float): the number of degrees to rotate
            speed (float): the rotation speed, in degrees per second (absolute value considered)
            on_start: see :py:meth:`travel`
            on_complete: see :py:meth:`travel`
            on_stalled: see :py:meth:`travel`
            callback_args: see :py:meth:`travel`

        Returns:
            MotionMonitor: the motion monitoring object
        """
        pulses_per_sec = self._pulses_per_sec_angular(speed or self._rotate_speed)

        for m in self._motors:
            m.speed_regulation_enabled = m.SPEED_REGULATION_ON
            m.speed_sp = pulses_per_sec

        pulses = round(angle / self._rotation_per_pulse)
        self._left_motor.position_sp = -pulses
        self._right_motor.position_sp = pulses

        self._motors_sync_start(RegulatedMotor.COMMAND_RUN_TO_REL_POS)

        monitor = MotionMonitor(self,
                                on_start=on_start,
                                on_complete=on_complete,
                                on_stalled=on_stalled,
                                callback_args=callback_args
                                )
        monitor.start()

        return monitor

    def rotate_forever(self, speed):
        """ Rotates in place forever.

        Args:
            speed (float): the rotation speed in degrees per second. Positive speed turns CCW, negative CW.
        """
        pulses_per_sec = self._pulses_per_sec_angular(speed)

        for m, direction in zip(self._motors, (-1, +1)):
            m.speed_regulation_enabled = m.SPEED_REGULATION_ON
            m.speed_sp = pulses_per_sec * direction

        self._motors_sync_start(RegulatedMotor.COMMAND_RUN_FOREVER)

    def rotate_right(self, angle, **kwargs):
        """ Convenience shortcut to avoid taking care of the angle sign.

        The sign if the passed angle value is discarded.

        .. seealso::

            :py:meth:`rotate`
        """
        return self.rotate(-abs(angle), **kwargs)

    def rotate_left(self, angle, **kwargs):
        """ Same as :py:meth:`rotate_right` in the opposite direction.
        """
        return self.rotate(abs(angle), **kwargs)

    def arc(self, radius, angle, speed=None, on_start=None, on_complete=None, on_stalled=None, callback_args=None):
        """ Moves the robot along an arc with a specified radius and angle, after which the robot stops moving.

        If radius is positive, the robot turns left, the center of the circle being on its left side. If it
        is negative, the move takes place on the opposite side. If radius is null, the robot rotates in place.

        The sign of the angle gives the direction of the spin (CCW if positive, CW if negative). Hence the combined
        signs of radius and angle specify the direction of move (forward or backward) along the arc. If both are
        the same, the robot will move forward. If they are different it will move backwards.

        The robot will stop when its heading has changed by the provided angle.

        .. note::

            In case of rotation in place (null radius), the currently set angular speed is used.

            If provided, the sign of the speed will be ignored, since inferred by the ones of radius and angle.

        Args:
            radius (float): radius of the arc, 0 for a rotation in place
            angle (float): the heading change
            speed (float): the speed along the path, if different from default one
            on_start, on_on_complete, on_stalled, callback_args: see :py:meth:`drive`

        Returns:
            MotionMonitor: the motion monitoring object
        """
        if radius == 0:
            return self.rotate(
                angle=angle,
                on_start=on_start,
                on_complete=on_complete,
                on_stalled=on_stalled,
                callback_args=callback_args
            )

        speed = abs(speed or self._travel_speed)
        tw_2 = float(self._track_width) / 2

        sides = (-1, 1)

        bias = tw_2 / radius
        speeds = (speed * (1 + side * bias) for side in sides)

        rd = math.radians(angle)
        distances = ((radius + side * tw_2) * rd for side in sides)

        for m, s, d in zip(self._motors, speeds, distances):
            m.speed_regulation_enabled = m.SPEED_REGULATION_ON
            m.speed_sp = self._pulses_per_sec_linear(s)
            m.position_sp = d / self._dist_per_pulse

        self._motors_sync_start(RegulatedMotor.COMMAND_RUN_TO_REL_POS)

        monitor = MotionMonitor(self,
                                on_start=on_start,
                                on_complete=on_complete,
                                on_stalled=on_stalled,
                                callback_args=callback_args
                                )
        monitor.start()

        return monitor

    def travel_arc(self, radius, distance, speed=None,
                   on_start=None, on_complete=None, on_stalled=None, callback_args=None):
        """ Similar to :py:meth:`arc` but specifying the distance along the arc instead of the turn angle.
        """
        if radius == 0:
            raise ValueError('invalid radius for travel_arc')

        angle = float(distance) / radius
        return self.arc(
            radius=radius,
            angle=angle,
            speed=speed,
            on_start=on_start,
            on_complete=on_complete,
            on_stalled=on_stalled,
            callback_args=callback_args
        )

    def steer(self, turn_rate, speed=None):
        """ Starts the robot moving forward along a curved path. This method is similar to the :py:meth:`arc`
        except it uses the `turn_rate` parameter do determine the curvature of the path and therefore has
        the ability to drive straight.

        `turn_rate` specifies the sharpness of the turn. Use values between -200 and +200.
        A positive (resp. negative) value means that the center of the turn is on the left (resp. right).

        This parameter determines the ratio of inner wheel speed to outer wheel speed as a percent.
        The formula used is : `ratio = 100 - abs(turn_rate)`. When `turn_rate` absolute value is greater than
        200, the ratio becomes negative, which means that the wheels will turn in opposite directions.
        The extreme values (-200 and +200) result in the robot turning in place (i.e. spinning on itself).

        Args:
            turn_rate (float): path turn rate
            speed (float): optional travel speed, used to override locally the current value
                of :py:attr:`travel_speed`. If positive (resp. negative), the robot moves forward (resp. backward)
        """
        if not turn_rate:
            self.drive(speed)

        else:
            # clip parameter in [-200, +200] range
            turn_rate = min(max(turn_rate, -200), 200)

            if abs(turn_rate) == 200:
                self.rotate_forever(speed)

            else:
                ratio = float(100 - abs(turn_rate))
                if turn_rate > 0:
                    speeds = speed * ratio, speed   # left turn => right wheel is the fastest and runs at 'speed'
                else:
                    speeds = speed, speed * ratio

                for m, s in zip(self._motors, speeds):
                    m.speed_regulation_enabled = m.SPEED_REGULATION_ON
                    m.speed_sp = self._pulses_per_sec_linear(s)

                self._motors_sync_start(RegulatedMotor.COMMAND_RUN_FOREVER)

    def steer_angle(self, turn_rate, angle, speed=None,
                    on_start=None, on_complete=None, on_stalled=None, callback_args=None):
        """ Same as :py:meth:`steer`, but ends the move after the robot has turned a given angle.

        Since the steering direction is defined by the turn rate, the sign of the angle is
        ignored.

        Args:
            turn_rate (float): see :py:meth:`steer`
            angle (float): steer angle in degrees
            speed (float): see :py:meth:`steer`
            on_start, on_complete, on_stalled, callback_args: see :py:meth:`steer`

        Returns:
            MotionMonitor: the motion monitoring object
        """
        # TODO compute the radius based on the turn rate and fall back to :py:meth:`arc`


class MotionMonitor(threading.Thread):
    """ An instance of this class is returned by pilot motion commands.

    It extends the standard :py:class:`threading.Thread` class by adding
    a couple of convenience methods and properties.
    """
    def __init__(self, pilot, on_start=None, on_complete=None, on_stalled=None, callback_args=None, **kwargs):
        """ All the callbacks receive the pilot as first argument, and can accept
        additional keyword parameters, which will contain the content
        of the `callback_args` dictionary passed here.

        Args:
            pilot (BasePilot): the associated pilot
            on_start (callable): an optional callback invoked when starting the motion
            on_complete (callable): an optional callback invoked at the normal completion of the motion.
            on_stalled (callable): an optional callback invoked when a motor stalled situation is detected
            callback_args (dict): an optional dictionary defining the kwargs which will be passed to the callbacks.
            \**kwargs: transmitted to super
        """
        super(MotionMonitor, self).__init__(**kwargs)
        self._pilot = pilot
        self._on_start = on_start
        self._on_complete = on_complete
        self._on_stalled = on_stalled
        self._callback_args = callback_args or {}
        self._stalled = False
        self._stopped = False

    @property
    def stalled(self):
        """ Tells if the motion was interrupted by a motor being stalled.

        :type: bool
        """
        return self._stalled

    @property
    def running(self):
        """ Tells if the motion is still ongoing..

        Can be used to test if it could complete within the wait delay.

        :type: bool
        """
        return self.is_alive()

    def wait(self, delay=60):
        """ Wait for the motion to be complete.

        Extends the inherited :py:meth:`threading.Thread.join` method by
        adding a default delay value. Although discouraged, it is allowed
        to pass `None` for a forever wait.

        The monitoring loop is stopped in case of timeout, to avoid
        callbacks being called at some later moment.

        Args:
            delay (float): the maximum wait time, in seconds.
        Returns:
            the instance, so the call can be chained with the motion command,
            while still returning the monitor to the caller
        """
        self.join(delay)
        if self.is_alive():
            self._stopped = True
        return self

    def stop(self):
        """ Stops the monitor and waits for the thread to end.
        """
        self._stopped = True
        self.join()

    def run(self):
        if self._on_start:
            self._on_start(self._pilot, **self._callback_args)

        motors = self._pilot._motors
        prev_positions = None

        while not self._stopped:
            s_p = [(_m.state, _m.position) for _m in motors]

            # if both motors are holding their position, it means that they have reached the goal
            if all(('holding' in s for s, _ in s_p)):
                if self._on_complete:
                    self._on_complete(self._pilot, **self._callback_args)
                return

            # check if one of the motors is not stalled, by comparing the current positions
            # and the previous ones (if available)
            # TODO find why the speed cannot be used (always 0)
            if prev_positions and any((pp == sp[1] and 'holding' not in sp[0] for pp, sp in zip(prev_positions, s_p))):
                # print('prev_positions=%s' % prev_positions)
                # print('s_p=%s' % s_p)
                # print('> stalled')
                self._stalled = True
                if self._on_stalled:
                    self._on_stalled(self._pilot, **self._callback_args)
                return

            prev_positions = [p for _, p in s_p]
            time.sleep(0.1)


class NullMotionMonitor(object):
    """ A dummy monitor imitating real ones methods and used for handling special
    cases resulting in null motions.
    """
    def wait(self, *kwargs):
        return self

    def stop(self):
        pass

    @property
    def running(self):
        return False

    @property
    def stalled(self):
        return False
