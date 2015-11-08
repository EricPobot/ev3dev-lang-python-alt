# -*- coding: utf-8 -*-

import os
from struct import unpack

from ev3dev.core import Device, ButtonBase


class Sensor(Device):
    """ The sensor class provides a uniform interface for using most of the
    sensors available for the EV3. The various underlying device drivers will
    create a `lego-sensor` device for interacting with the sensors.

    Sensors are primarily controlled by setting the `mode` and monitored by
    reading the `value<N>` attributes. Values can be converted to floating point
    if needed by `value<N>` / 10.0 ^ `decimals`.

    Since the name of the `sensor<N>` device node does not correspond to the port
    that a sensor is plugged in to, you must look at the `port_name` attribute if
    you need to know which port a sensor is plugged in to. However, if you don't
    have more than one sensor of each type, you can just look for a matching
    `driver_name`. Then it will not matter which port a sensor is plugged in to - your
    program will still work.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    _bin_data_sizes = {
        "u8":     1,
        "s8":     1,
        "u16":    2,
        "s16":    2,
        "s16_be": 2,
        "s32":    4,
        "float":  4
    }

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

        # will be initialized on first read on binary data
        self._bin_data_size = None

    @property
    def command(self):
        """ str: sensor command

        This property is write-only.
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self.set_attr_string('command', value)

    @property
    def commands(self):
        """ list[str]: the list of the valid commands for the sensor.

        Returns -EOPNOTSUPP if no commands are supported.
        """
        return self.get_attr_set('commands')

    @property
    def decimals(self):
        """ int: the number of decimal places for the values in the `value<N>`
        attributes of the current mode.
        """
        return self.get_attr_int('decimals')

    @property
    def driver_name(self):
        """ str: the name of the sensor device/driver.

        See the list of [supported sensors] for a complete list of drivers.
        """
        return self.get_attr_string('driver_name')

    @property
    def mode(self):
        """ str: the current mode.

        Writing one of the values returned by `modes` sets the sensor to that mode.
        """
        return self.get_attr_string('mode')

    @mode.setter
    def mode(self, value):
        self.set_attr_string('mode', value)

    @property
    def modes(self):
        """ list[str]: the list of the valid modes for the sensor.
        """
        return self.get_attr_set('modes')

    @property
    def num_values(self):
        """ int: the number of `value<N>` attributes that will return a valid value
        for the current mode.
        """
        return self.get_attr_int('num_values')

    @property
    def port_name(self):
        """ str:the name of the port the sensor is connected to, e.g. `ev3:in1`.

        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.
        """
        return self.get_attr_string('port_name')

    @property
    def units(self):
        """ str: the units of the measured value for the current mode. May return
        an empty string
        """
        return self.get_attr_string('units')

    def value(self, n=0):
        """ Returns the (optionally indexed) sensor value.

        Args:
            n (Optional[int]): the index of the value for multiple outputs sensors

        Returns:
            int: the value
        """
        try:
            return self.get_attr_int('value%d' % int(n))
        except ValueError:
            return 0

    @property
    def bin_data_format(self):
        """ str: the format of the values in `bin_data` for the current mode.

        Possible values are:

        - `u8`: Unsigned 8-bit integer (byte)
        - `s8`: Signed 8-bit integer (sbyte)
        - `u16`: Unsigned 16-bit integer (ushort)
        - `s16`: Signed 16-bit integer (short)
        - `s16_be`: Signed 16-bit integer, big endian
        - `s32`: Signed 32-bit integer (int)
        - `float`: IEEE 754 32-bit floating point (float)
        """
        return self.get_attr_string('bin_data_format')

    def bin_data(self, fmt=None):
        """ Returns the unscaled raw values in the `value<N>` attributes as raw byte
        array. Use `bin_data_format`, `num_values` and the individual sensor
        documentation to determine how to interpret the data.

        Args:
            fmt (str): format to be used for unpacking the raw bytes into a struct.

        Example:

            >>> from ev3dev import *
            >>> ir = InfraredSensor()
            >>> ir.value()
            28
            >>> ir.bin_data('<b')
            (28,)
        """
        if not self._bin_data_size:
            self._bin_data_size = self._bin_data_sizes.get(self.bin_data_format, 1) * self.num_values

        f = self._attribute_cache.file_handle('/bin_data', binary=True)
        f.seek(0)
        raw = bytearray(f.read(self._bin_data_size))

        if fmt:
            return unpack(fmt, raw)
        else:
            return raw


class I2cSensor(Sensor):
    """ A generic interface to control I2C-type EV3 sensors.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['nxt-i2c-sensor'], **kwargs)

    @property
    def fw_version(self):
        """
        Returns the firmware version of the sensor if available. Currently only
        I2C/NXT sensors support this.
        """
        return self.get_attr_string('fw_version')

    @property
    def poll_ms(self):
        """ int: the polling period of the sensor in milliseconds.

        Setting it to 0 disables polling. The minimum value is hard
        coded as 50 msec. Returns -EOPNOTSUPP if changing polling is not supported.
        Currently only I2C/NXT sensors support changing the polling period.
        """
        return self.get_attr_int('poll_ms')

    @poll_ms.setter
    def poll_ms(self, value):
        self.set_attr_int('poll_ms', value)


class ColorSensor(Sensor):
    """ LEGO EV3 color sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-color'], **kwargs)

    # Reflected light. Red LED on.
    MODE_COL_REFLECT = 'COL-REFLECT'

    # Ambient light. Red LEDs off.
    MODE_COL_AMBIENT = 'COL-AMBIENT'

    # Color. All LEDs rapidly cycling, appears white.
    MODE_COL_COLOR = 'COL-COLOR'

    # Raw reflected. Red LED on
    MODE_REF_RAW = 'REF-RAW'

    # Raw Color Components. All LEDs rapidly cycling, appears white.
    MODE_RGB_RAW = 'RGB-RAW'


class UltrasonicSensor(Sensor):
    """ LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)

    # Continuous measurement in centimeters.
    # LEDs: On, steady
    MODE_US_DIST_CM = 'US-DIST-CM'

    # Continuous measurement in inches.
    # LEDs: On, steady
    MODE_US_DIST_IN = 'US-DIST-IN'

    # Listen.  LEDs: On, blinking
    MODE_US_LISTEN = 'US-LISTEN'

    # Single measurement in centimeters.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_CM = 'US-SI-CM'

    # Single measurement in inches.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_IN = 'US-SI-IN'


class GyroSensor(Sensor):
    """ LEGO EV3 gyro sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-gyro'], **kwargs)

    # Angle
    MODE_GYRO_ANG = 'GYRO-ANG'

    # Rotational speed
    MODE_GYRO_RATE = 'GYRO-RATE'

    # Raw sensor value
    MODE_GYRO_FAS = 'GYRO-FAS'

    # Angle and rotational speed
    MODE_GYRO_G_A = 'GYRO-G&A'

    # Calibration ???
    MODE_GYRO_CAL = 'GYRO-CAL'


class InfraredSensor(Sensor):
    """ LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-ir'], **kwargs)

    # Proximity
    MODE_IR_PROX = 'IR-PROX'

    # IR Seeker
    MODE_IR_SEEK = 'IR-SEEK'

    # IR Remote Control
    MODE_IR_REMOTE = 'IR-REMOTE'

    # IR Remote Control. State of the buttons is coded in binary
    MODE_IR_REM_A = 'IR-REM-A'

    # Calibration ???
    MODE_IR_CAL = 'IR-CAL'


class SoundSensor(Sensor):
    """ LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-sound'], **kwargs)

    # Sound pressure level. Flat weighting
    MODE_DB = 'DB'

    # Sound pressure level. A weighting
    MODE_DBA = 'DBA'


class LightSensor(Sensor):
    """ LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-light'], **kwargs)

    # Reflected light. LED on
    MODE_REFLECT = 'REFLECT'

    # Ambient light. LED off
    MODE_AMBIENT = 'AMBIENT'


class TouchSensor(Sensor):
    """ Touch Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)


class RemoteControl(ButtonBase):
    """
    EV3 Remote Controller
    """

    _BUTTON_VALUES = {
            0: [],
            1: ['red_up'],
            2: ['red_down'],
            3: ['blue_up'],
            4: ['blue_down'],
            5: ['red_up', 'blue_up'],
            6: ['red_up', 'blue_down'],
            7: ['red_down', 'blue_up'],
            8: ['red_down', 'blue_down'],
            9: ['beacon'],
            10: ['red_up', 'red_down'],
            11: ['blue_up', 'blue_down']
            }

    on_red_up = None
    on_red_down = None
    on_blue_up = None
    on_blue_down = None
    on_beacon = None

    @property
    def red_up(self):
        """
        Checks if `red_up` button is pressed.
        """
        return 'red_up' in self.buttons_pressed

    @property
    def red_down(self):
        """
        Checks if `red_down` button is pressed.
        """
        return 'red_down' in self.buttons_pressed

    @property
    def blue_up(self):
        """
        Checks if `blue_up` button is pressed.
        """
        return 'blue_up' in self.buttons_pressed

    @property
    def blue_down(self):
        """
        Checks if `blue_down` button is pressed.
        """
        return 'blue_down' in self.buttons_pressed

    @property
    def beacon(self):
        """
        Checks if `beacon` button is pressed.
        """
        return 'beacon' in self.buttons_pressed

    def __init__(self, sensor=None, channel=1):
        if sensor is None:
            self._sensor = InfraredSensor()
        else:
            self._sensor = sensor

        self._channel = max(1, min(4, channel)) - 1
        self._state = set([])

        if self._sensor.connected:
            self._sensor.mode = 'IR-REMOTE'

    @property
    def buttons_pressed(self):
        """
        Returns list of currently pressed buttons.
        """
        return RemoteControl._BUTTON_VALUES.get(self._sensor.value(self._channel), [])