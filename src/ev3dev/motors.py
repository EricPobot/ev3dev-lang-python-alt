# -*- coding: utf-8 -*-

from ev3dev.core import Device


class BaseMotor(Device):
    """ The root class containing definitions shared by the different types of motors
    provided in this module.

    :py:attr:`SYSTEM_CLASS_NAME` and :py:attr:`SYSTEM_DEVICE_NAME_CONVENTION` must be defined by
    concrete sub-classes to allow the binding with `/sys/class` tree.
    """

    #: The system class of this device, i.e. the subdirectory of `/sys/class` in which instances
    #: sub-tree is defined
    SYSTEM_CLASS_NAME = None

    #: The name or pattern used to identify instances of this device
    SYSTEM_DEVICE_NAME_CONVENTION = None

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        """
        Args:
            port (str): the port the motor is connected to. Can be omitted if only one motor is
                used, since the `Device` initialization will find it by scanning.
            name (str): the pattern for finding the device entry in `/sys/class`
            **kwargs: additional arguments passed to super class

        Raises:
            NotImplementedError: if mandatory constants are not defined
        """
        if not (self.SYSTEM_CLASS_NAME and self.SYSTEM_DEVICE_NAME_CONVENTION):
            raise NotImplementedError()

        if port:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

    @property
    def polarity(self):
        """ The motor polarity.

        With `normal` polarity, a positive duty cycle will cause the motor to rotate clockwise.
        With `inversed` polarity, a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are `normal` and `inversed`.

        :type: int
        """
        return self.get_attr_string('polarity')

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string('polarity', value)

    @property
    def state(self):
        """ The list of state flags.

        Possible flags are `running`, `ramping` `holding` and `stalled`, but which of them
        are returned depend on the concrete sub-class. Refer to their documentation.

        :type: list[str]
        """
        return self.get_attr_set('state')


class PositionControlMixin(object):
    """ Mixin class defining position related properties which are shared by several implementations.

    The exact meaning of the position value depends on the device. Refer the association classes for
    detail.
    """
    @property
    def position_sp(self):
        """ The motor target position.

        The exact meaning of the position value depends on the device. Refer the association classes for
        detail.

        :type: int
        """
        # do not care about get_attr_int being tagged as undefined by IDEs, since this mixin is used
        # only in Device sub-classes
        return self.get_attr_int('position_sp')

    @position_sp.setter
    def position_sp(self, value):
        self.set_attr_int('position_sp', value)


class DcMotor(BaseMotor):
    """ The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.

    Commands available for DC motors are :
        - `run-forever` will cause the motor to run until another command is sent.
        - `run-timed` will run the motor for the amount of time specified in `time_sp`
          and then stop the motor using the command specified by `stop_command`.
        - `run-direct` will run the motor at the duty cycle specified by `duty_cycle_sp`.
          Unlike other run commands, changing `duty_cycle_sp` while running *will*
          take effect immediately.
        - `stop` will stop any of the run commands before they are complete using the
          command specified by `stop_command`.

    These commands are available as the constants named `COMMAND_xxx`.

    The duty cycle is initialized to 75 so that instances are ready to use after
    their instantiation.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)
        if 'duty_cycle_sp' not in kwargs:
            self.duty_cycle_sp = 75

    @property
    def duty_cycle(self):
        """ The current duty cycle of the motor. Units are percent. Values
        are -100 to 100.

        :type: int
        """
        return self.get_attr_int('duty_cycle')

    @property
    def duty_cycle_sp(self):
        """ The duty cycle setpoint.

        Units are in percent. Valid values are -100 to 100. A negative value causes
        the motor to rotate in reverse. This value is only used when `speed_regulation`
        is off.

        :type: int
        """
        return self.get_attr_int('duty_cycle_sp')

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self.set_attr_int('duty_cycle_sp', value)

    @property
    def ramp_up_sp(self):
        """ The ramp up setpoint.

        Units are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 0 to 100% duty cycle over the span of this setpoint
        when starting the motor. If the maximum duty cycle is limited by `duty_cycle_sp`
        or speed regulation, the actual ramp time duration will be less than the setpoint.

        :type: int
        """
        return self.get_attr_int('ramp_up_sp')

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self.set_attr_int('ramp_up_sp', value)

    @property
    def ramp_down_sp(self):
        """ The ramp down setpoint.

        Units are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 100% duty cycle down to 0 over the span of this setpoint
        when stopping the motor. If the starting duty cycle is less than 100%, the
        ramp time duration will be less than the full span of the setpoint.

        :type: int
        """
        return self.get_attr_int('ramp_down_sp')

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self.set_attr_int('ramp_down_sp', value)

    @property
    def stop_command(self):
        """ The behavior for the `stop` command.

        The value determines the motors behavior when `command` is set to `stop`.
        Also, it determines the motors behavior when a run command completes. See
        `stop_commands` for a list of possible values.

        :type: str
        """
        return self.get_attr_string('stop_command')

    @stop_command.setter
    def stop_command(self, value):
        self.set_attr_string('stop_command', value)

    @property
    def stop_commands(self):
        """ The list of stop modes supported by the motor controller.

        Possible values are :

        - `coast` means that power will be removed from the motor and it will freely coast to a stop

        - `brake` means that power will be removed from the motor and a passive electrical load will
          be placed on the motor. This is usually done by shorting the motor terminals together.
          This load will absorb the energy from the rotation of the motors and cause the motor to stop
          more quickly than coasting.

        - `hold` does not remove power from the motor. Instead it actively try to hold the motor at the current
          position. If an external force tries to turn the motor, the motor will 'push back' to maintain its position.

        `hold` is available for regulated motors only

        :type: list[str]
        """
        return self.get_attr_set('stop_commands')

    @property
    def time_sp(self):
        """ The amount of time the motor will run when using the
        `run-timed` command.

        Units are in milliseconds.

        :type: int
        """
        return self.get_attr_int('time_sp')

    @time_sp.setter
    def time_sp(self, value):
        self.set_attr_int('time_sp', value)

    #: Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    #: Run the motor for the amount of time specified in `time_sp`
    #: and then stop the motor using the command specified by `stop_command`.
    COMMAND_RUN_TIMED = 'run-timed'

    #: Run the motor at the duty cycle specified by `duty_cycle_sp`.
    #: Unlike other run commands, changing `duty_cycle_sp` while running *will*
    #: take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    #: Stop any of the run commands before they are complete using
    #: the command specified by `stop_command`.
    COMMAND_STOP = 'stop'

    #: With `normal` polarity, a positive duty cycle will cause
    #: the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With `inversed` polarity, a positive duty cycle will cause
    #: the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    #: Power will be removed from the motor and it will freely coast to a stop.
    STOP_COMMAND_COAST = 'coast'

    #: Power will be removed from the motor and a passive electrical load will
    #: be placed on the motor. This is usually done by shorting the motor terminals
    #: together. This load will absorb the energy from the rotation of the motors and
    #: cause the motor to stop more quickly than coasting.
    STOP_COMMAND_BRAKE = 'brake'

    def run_forever(self, **kwargs):
        """Runs the motor until another command is sent.

        Args:
            \**kwargs: additional arguments for the command
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_FOREVER

    def run_timed(self, time_sp, **kwargs):
        """ Runs the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.

        Args:
            time_sp (int): number of milliseconds to run the motor
            \**kwargs: additional options for the command
        """
        self.time_sp = time_sp
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TIMED

    def run_direct(self, duty_cycle_sp, **kwargs):
        """ Runs the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.

        Args:
            duty_cycle_sp (int): target duty cycle
            \**kwargs: additional options for the command
        """
        self.duty_cycle_sp = duty_cycle_sp
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_DIRECT

    def stop(self, stop_command=None, **kwargs):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.

        Args:
            stop_command (str): stop_command if different from the previously set one
            \**kwargs: additional options for the command
        """
        if stop_command:
            self.stop_command = stop_command
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_STOP


class RegulatedMotor(DcMotor, PositionControlMixin):
    """ The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors.

    As it shares the basic features with the un-regulated DC motor, it is implemented as a
    sub-class of it.

    Commands available for regulated motors are `DcMotor` ones, plus the following ones:

        - `run-to-abs-pos` will run to an absolute position specified by `position_sp`
          and then stop using the command specified in `stop_command`.
        - `run-to-rel-pos` will run to a position relative to the current `position` value.
          The new position will be current `position` + `position_sp`. When the new
          position is reached, the motor will stop using the command specified by `stop_command`.
        - `reset` will reset all of the motor parameter attributes to their default value.
          This will also have the effect of stopping the motor.

    The `position_sp` is expressed in encoder counts. You can use the value returned by `counts_per_rot`
    to convert encoder counts to/from rotations or degrees.
    """

    SYSTEM_CLASS_NAME = 'tacho-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    @property
    def count_per_rot(self):
        """ The number of encoder counts in one rotation of the motor.

        Encoder counts are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to encoder counts. In the case of linear
        actuators, the units here will be counts per centimeter.

        :type: int
        """
        return self.get_attr_int('count_per_rot')

    @property
    def encoder_polarity(self):
        """ Rotary encoder polarity.

        This is an advanced feature to all use of motors that send inversed encoder signals to the EV3.
        This should be set correctly by the driver of a device. You only need to change this value
        if you are using a unsupported device. Valid values are `normal` and `inversed`.

        :type: str
        """
        return self.get_attr_string('encoder_polarity')

    @encoder_polarity.setter
    def encoder_polarity(self, value):
        self.set_attr_string('encoder_polarity', value)

    @property
    def position(self):
        """ The current position of the motor in pulses of the rotary
        encoder.

        When the motor rotates clockwise, the position will increase.
        Likewise, rotating counter-clockwise causes the position to decrease.
        Writing will set the position to that value.

        :type: int
        """
        return self.get_attr_int('position')

    @position.setter
    def position(self, value):
        self.set_attr_int('position', value)

    @property
    def position_p(self):
        """ The proportional constant for the position PID.

        :type: int
        """
        return self.get_attr_int('hold_pid/Kp')

    @position_p.setter
    def position_p(self, value):
        self.set_attr_int('hold_pid/Kp', value)

    @property
    def position_i(self):
        """ The integral constant for the position PID.

        :type: int
        """
        return self.get_attr_int('hold_pid/Ki')

    @position_i.setter
    def position_i(self, value):
        self.set_attr_int('hold_pid/Ki', value)

    @property
    def position_d(self):
        """ The derivative constant for the position PID.

        :type: int
        """
        return self.get_attr_int('hold_pid/Kd')

    @position_d.setter
    def position_d(self, value):
        self.set_attr_int('hold_pid/Kd', value)

    @property
    def speed(self):
        """ The current motor speed in encoder counts per second.

        Not, this is not necessarily degrees (although it is for LEGO motors). Use the `count_per_rot`
        attribute to convert this value to RPM or deg/sec.

        :type: int
        """
        return self.get_attr_int('speed')

    @property
    def speed_sp(self):
        """ The target speed in encoder counts per second used when `speed_regulation` is on.

        Use the `count_per_rot` attribute to convert RPM or deg/sec to encoder counts per second.

        :type: int
        """
        return self.get_attr_int('speed_sp')

    @speed_sp.setter
    def speed_sp(self, value):
        self.set_attr_int('speed_sp', value)

    @property
    def speed_regulation_enabled(self):
        """ Turns speed regulation on or off.

        If speed regulation is on, the motor controller will vary the power supplied to the motor to try
        to maintain the speed specified in `speed_sp`. If speed regulation is off, the controller
        will use the power specified in `duty_cycle_sp`. Valid values are `on` and `off`.

        :type: str
        """
        return self.get_attr_string('speed_regulation')

    @speed_regulation_enabled.setter
    def speed_regulation_enabled(self, value):
        self.set_attr_string('speed_regulation', value)

    @property
    def speed_regulation_p(self):
        """ The proportional constant for the speed regulation PID.

        :type: int
        """
        return self.get_attr_int('speed_pid/Kp')

    @speed_regulation_p.setter
    def speed_regulation_p(self, value):
        self.set_attr_int('speed_pid/Kp', value)

    @property
    def speed_regulation_i(self):
        """ The integral constant for the speed regulation PID.

        :type: int
        """
        return self.get_attr_int('speed_pid/Ki')

    @speed_regulation_i.setter
    def speed_regulation_i(self, value):
        self.set_attr_int('speed_pid/Ki', value)

    @property
    def speed_regulation_d(self):
        """ The derivative constant for the speed regulation PID.

        :type: int
        """
        return self.get_attr_int('speed_pid/Kd')

    @speed_regulation_d.setter
    def speed_regulation_d(self, value):
        self.set_attr_int('speed_pid/Kd', value)

    #: Run to an absolute position specified by `position_sp` and then
    #: stop using the command specified in `stop_command`.
    COMMAND_RUN_TO_ABS_POS = 'run-to-abs-pos'

    #: Run to a position relative to the current `position` value.
    #: The new position will be current `position` + `position_sp`.
    #: When the new position is reached, the motor will stop using
    #: the command specified by `stop_command`.
    COMMAND_RUN_TO_REL_POS = 'run-to-rel-pos'

    #: Reset all of the motor parameter attributes to their default value.
    #: This will also have the effect of stopping the motor.
    COMMAND_RESET = 'reset'

    #: Sets the normal polarity of the rotary encoder.
    ENCODER_POLARITY_NORMAL = 'normal'

    #: Sets the inversed polarity of the rotary encoder.
    ENCODER_POLARITY_INVERSED = 'inversed'

    #: The motor controller will vary the power supplied to the motor
    #: to try to maintain the speed specified in `speed_sp`.
    SPEED_REGULATION_ON = 'on'

    #: The motor controller will use the power specified in `duty_cycle_sp`.
    SPEED_REGULATION_OFF = 'off'

    #: Does not remove power from the motor. Instead it actively try to hold the motor
    #: at the current position. If an external force tries to turn the motor, the motor
    #: will ``push back`` to maintain its position.
    STOP_COMMAND_HOLD = 'hold'

    def run_to_abs_pos(self, position_sp, **kwargs):
        """ Runs to an absolute position specified by `position_sp` and then
        stop using the command specified in `stop_command`.

        Args:
            position_sp (int): the target position in encoder units
            \**kwargs: additional arguments for the command
        """
        self.position_sp = position_sp
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_ABS_POS

    def run_to_rel_pos(self, position_sp, **kwargs):
        """ Runs to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`.
        When the new position is reached, the motor will stop using
        the command specified by `stop_command`.

        Args:
            position_sp (int): the target position in encoder units
            \**kwargs: additional options for the command
        """
        self.position_sp = position_sp
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = self.COMMAND_RUN_TO_REL_POS

    def reset(self):
        """ Resets all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        self.command = self.COMMAND_RESET


class LargeMotor(RegulatedMotor):
    """ EV3 large servo motor.
    """

    def __init__(self, port=None, name=RegulatedMotor.SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        super(LargeMotor, self).__init__(port, name, driver_name=['lego-ev3-l-motor'], **kwargs)


class MediumMotor(RegulatedMotor):
    """ EV3 medium servo motor.
    """

    def __init__(self, port=None, name=RegulatedMotor.SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        super(MediumMotor, self).__init__(port, name, driver_name=['lego-ev3-m-motor'], **kwargs)


class ServoMotor(BaseMotor, PositionControlMixin):
    """ The servo motor class provides a uniform interface for using hobby type
    servo motors.

    States returned by this class of motor :

        - `running`: means that the servo is powered

    The `position_sp` property units are percent. Valid values are -100 to 100 (-100% to 100%) where `-100`
    corresponds to `min_pulse_sp`, `0` corresponds to `mid_pulse_sp` and `100` corresponds to `max_pulse_sp`.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    @property
    def max_pulse_sp(self):
        """ The pulse size in milliseconds for the signal that tells the
        servo to drive to the maximum (clockwise) position_sp. Default value is 2400.

        Valid values are 2300 to 2700. You must write to the position_sp attribute for
        changes to this attribute to take effect.

        :type: int
        """
        return self.get_attr_int('max_pulse_sp')

    @max_pulse_sp.setter
    def max_pulse_sp(self, value):
        self.set_attr_int('max_pulse_sp', value)

    @property
    def mid_pulse_sp(self):
        """ The pulse size in milliseconds for the signal that tells the
        servo to drive to the mid position_sp. Default value is 1500.

        Valid values are 1300 to 1700. For example, on a 180 degree servo, this would be
        90 degrees. On continuous rotation servo, this is the 'neutral' position_sp
        where the motor does not turn. You must write to the position_sp attribute for
        changes to this attribute to take effect.

        :type: int
        """
        return self.get_attr_int('mid_pulse_sp')

    @mid_pulse_sp.setter
    def mid_pulse_sp(self, value):
        self.set_attr_int('mid_pulse_sp', value)

    @property
    def min_pulse_sp(self):
        """ The pulse size in milliseconds for the signal that tells the
        servo to drive to the miniumum (counter-clockwise) position_sp. Default value
        is 600.

        Valid values are 300 to 700. You must write to the position_sp
        attribute for changes to this attribute to take effect.

        :type: int
        """
        return self.get_attr_int('min_pulse_sp')

    @min_pulse_sp.setter
    def min_pulse_sp(self, value):
        self.set_attr_int('min_pulse_sp', value)

    @property
    def rate_sp(self):
        """ The rate at which the servo should travel from 0 to 100.0% (half of the full
        range of the servo). Units are in milliseconds.

        Example:
          Setting the rate_sp to 1000 means that it will take a 180 degree servo
          2 second to move from 0 to 180 degrees.

        .. Note:: Some servo controllers may not support this in which
          case reading and writing will fail with `-EOPNOTSUPP`. In continuous rotation
          servos, this value will affect the rate_sp at which the speed ramps up or down.

        :type: int
        """
        return self.get_attr_int('rate_sp')

    @rate_sp.setter
    def rate_sp(self, value):
        self.set_attr_int('rate_sp', value)

    #: Drive servo to the position set in the `position_sp` attribute.
    COMMAND_RUN = 'run'

    #: Remove power from the motor.
    COMMAND_FLOAT = 'float'

    #: With `normal` polarity, a positive duty cycle will cause the motor
    #: to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    #: With `inversed` polarity, a positive duty cycle will cause the motor
    #: to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    def run(self, **kwargs):
        """ Drives the servo to the position set in the `position_sp` attribute.

        Args:
            \**kwargs: additional arguments for the command
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run'

    def float(self, **kwargs):
        """ Removes the power from the motor.

        Args:
            \**kwargs: additional arguments for the command
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'float'
