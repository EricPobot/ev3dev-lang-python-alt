# -----------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel <rhempel@hempeldesigngroup.com>
# Copyright (c) 2015 Anton Vanhoucke <antonvh@gmail.com>
# Copyright (c) 2015 Denis Demidov <dennis.demidov@gmail.com>
# Copyright (c) 2015 Eric Pascual <eric@pobot.org>
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-

import array
import fcntl
import fnmatch
import os
import os.path
import re
from collections import namedtuple
import threading
import time

INPUT_AUTO = ''
OUTPUT_AUTO = ''


class FileCache(object):
    """ Attribute reader/writer with cached file access
    """
    def __init__(self):
        self._cache = {}

    def __del__(self):
        for f in self._cache.values():
            f.close()

    def file_handle(self, path, binary=False):
        """ Manages the file handle cache and opening the files in the correct mode.

        Args:
            path (str): the file path of the attribute
            binary (Optional[bool]): True if the attribute value is binary. Default to False

        Returns:
            file: the opened file object

        Raises:
            ValueError: if the provided path does not exist
        """
        try:
            return self._cache[path]

        except KeyError:
            self._cache[path] = f = self._open_file(path, binary)
            return f

    @staticmethod
    def _open_file(path, binary):
        if not os.path.exists(path):
            raise ValueError('path not found: %s' % path)

        r_ok = os.access(path, os.R_OK)
        w_ok = os.access(path, os.W_OK)

        if r_ok and w_ok:
            mode = 'a+'
        elif w_ok:
            mode = 'a'
        else:
            mode = 'r'

        if binary:
            mode += 'b'

        # print('opening %s with mode %s' % (path, mode))
        return open(path, mode, 0)

    def read(self, path):
        """ Gets the attribute value.

        The type of the returned value depends on the value of the `binary` flag passed
        to ``file_handle`` method.

        Args:
            path (str): the attribute file path

        Returns:
            the attribute value.
        """
        f = self.file_handle(path)

        f.seek(0)
        return f.read().strip()

    def write(self, path, value):
        """ Sets the attribute value.
        Args:
            path (str): the attribute file path
            value: the attribute value
        """
        f = self.file_handle(path)

        f.seek(0)
        f.write(value)


class DeviceFileCache(FileCache):
    """ A specialized file cache dealing with attributes file of a given device.

    To avoid having the full path being computed by caller each time an attribute is
    accessed, we factor it here when opening the file, and use the attribute name as
    the cache key.
    """
    def __init__(self, device_classpath):
        """
        Args:
            device_classpath (str): the absolute path of the `/sys/class` sub-directory
            containing the device attribute files

        Raises:
            ValueError: if the provided path does not point to a directory
        """
        if not os.path.isdir(device_classpath):
            raise ValueError('device sysfs not found')

        super(DeviceFileCache, self).__init__()
        self._device_classpath = device_classpath

    def file_handle(self, attribute_name, binary=False):
        """ Returns the file handle for a given device attribute.

        Args:
            attribute_name (str): the name of the attribute
            binary (Optional[bool]): True if attribute value is binary. Default to False.

        Returns:
            file: the opened file object
        """
        try:
            return self._cache[attribute_name]
        except KeyError:
            path = os.path.join(self._device_classpath, attribute_name)
            self._cache[attribute_name] = f = self._open_file(path, binary)
            return f


class Device(object):
    """ The ev3dev device base class.

    Device implementation concrete classes must define the :py:attr:`SYSTEM_CLASS_NAME` attribute
    and can override :py:attr:`SYSTEM_DEVICE_NAME_CONVENTION` one for narrowing the pattern
    matched by implemented device names, used when no specific device name is provided.
    """

    #: The system class of this device, i.e. the subdirectory of `/sys/class` in which instances
    #: sub-tree is defined. Must be overridden by concrete sub-classes
    SYSTEM_CLASS_NAME = None

    #: The name or pattern used to identify instances of this device.
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    _DEVICE_ROOT_PATH = '/sys/class'

    _DEVICE_INDEX = re.compile(r'^.*(?P<idx>\d+)$')

    def __init__(self, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        """ Spin through the Linux `sysfs` class for the device type and find
        a device that matches the provided name and attributes (if any).

        Args:
            name (str): pattern that device name should match if different from
                :py:attr:`SYSTEM_DEVICE_NAME_CONVENTION`.
                For example, 'sensor*' or 'motor*'.
            \**kwargs: keyword arguments used for matching the corresponding device
                attributes. For example, port_name='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Examples:

            >>> d = Device('tacho-motor', port_name='outA')
            >>> s = Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected successfully, the `connected` attribute is set to True.

        Raises:
            NotImplementedError: if someone tris to instantiate us or any abstract descendant
        """
        if not self.SYSTEM_CLASS_NAME:
            # concrete classes must define the above constant
            # => if here we are trying to instantiate an abstract one
            raise NotImplementedError()

        sysclass_path = os.path.join(Device._DEVICE_ROOT_PATH, self.SYSTEM_CLASS_NAME)

        for file_name in os.listdir(sysclass_path):
            if fnmatch.fnmatch(file_name, name):
                self._path = os.path.join(sysclass_path, file_name)
                self._attribute_cache = DeviceFileCache(self._path)

                # See if all the requested attributes exist for the candidate device
                if all([self._matches(k, kwargs[k]) for k in kwargs]):
                    self.connected = True

                    match = Device._DEVICE_INDEX.match(file_name)
                    if match:
                        self._device_index = int(match.group('idx'))
                    else:
                        self._device_index = None

                    return

        self._path = ''
        self.connected = False
        self._attribute_cache = None

    def _matches(self, attribute, pattern):
        """Test if attribute value matches pattern (that is, if pattern is a
        substring of attribute value). If pattern is a list, then a match with
        any one entry is enough.

        Args:
            attribute (str): attribute name
            pattern: one or more accepted values

        Returns:
            True if matches
        """
        value = self._get_attribute(attribute)
        if isinstance(pattern, (list, tuple, set)):
            return any([value.find(pat) >= 0 for pat in pattern])
        else:
            return value.find(pattern) >= 0

    def _get_attribute(self, attribute):
        """ Internal device attribute getter """
        return self._attribute_cache.read(attribute)

    def _set_attribute(self, attribute, value):
        """ Internal device attribute setter """
        self._attribute_cache.write(attribute, value)

    # TODO do we really need these get/set_attr_xxx methods in Python ?
    def get_attr_int(self, attribute):
        """ Gets the value of an integer type attribute.

        Args:
            attribute (str): attribute name

        Returns:
            int: attribute value
        """
        return int(self._get_attribute(attribute))

    def set_attr_int(self, attribute, value):
        """ Sets the value of an integer type attribute.

        The method ensures the passed value is an integer.

        Args:
            attribute (str): attribute name
            value (int): attribute value

        Raises:
            ValueError: if the value is not an integer
        """
        self._set_attribute(attribute, str(int(value)))

    def get_attr_string(self, attribute):
        """ Gets the value of a string type attribute.

        Args:
            attribute (str): attribute name

        Returns:
            str: attribute value
        """
        return self._get_attribute(attribute)

    def set_attr_string(self, attribute, value):
        """ Sets the value of a string type attribute.

        The method ensures the written value is a string. In fact any
        type can be passed, since the value is converted to a string
        before writing.

        Args:
            attribute (str): attribute name
            value: attribute value

        Raises:
            ValueError: if the value is not an integer
        """
        self._set_attribute(attribute, str(value))

    def get_attr_set(self, attribute):
        """ Gets the value of a set type attribute.

        Args:
            attribute (str): attribute name

        Returns:
            list: attribute value
        """
        return self._attribute_cache.read(attribute).split()

    @property
    def device_index(self):
        return self._device_index

    @property
    def command(self):
        """ command sent to the motor controller. See `commands` for a list of
        possible values.

        .. Important:: This is a write-only property.

        :type: str
        """
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        self.set_attr_string('command', value)

    @property
    def commands(self):
        """ The list of commands that are supported by the motor
        controller.

        Refer to sub-classes documentation for details about their available commands.

        :type: list[str]
        """
        return self.get_attr_set('commands')

    @property
    def port_name(self):
        """ The name of the port that the device is connected to.

        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.

        :type: str
        """
        return self.get_attr_string('port_name')

    @property
    def driver_name(self):
        """ The name of the driver for this device.

        :type: str
        """
        return self.get_attr_string('driver_name')


class PluggedDevice(Device):
    """ Abstract model for any external device connected to the brick using one of its ports,
    which can be identified by its name (e.g. `in1`, `outA`).

    This class is used for factoring behaviors common to motors and sensors, and making explicit the
    definition of a port for such devices. It is not intended to be directly instantiated.
    """
    def __init__(self, port=None, **kwargs):
        """
        Args:
            port (str): optional port name
            **kwargs: keyword arguments passed to the base class
        """
        if port is not None:
            kwargs['port_name'] = port
        super(PluggedDevice, self).__init__(**kwargs)


class Led(Device):
    """ Any device controlled by the generic LED driver.

    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'

    TRIGGER_ON = 'default-on'
    TRIGGER_TIMER = 'timer'
    TRIGGER_HEARTBEAT = 'heartbeat'

    @property
    def max_brightness(self):
        """ The maximum allowable brightness value.

        :type: int
        """
        return self.get_attr_int('max_brightness')

    @property
    def brightness(self):
        """ The brightness level.

        Possible values are from 0 to `max_brightness`.

        :type: int
        """
        return self.get_attr_int('brightness')

    @brightness.setter
    def brightness(self, value):
        self.set_attr_int('brightness', value)

    @property
    def triggers(self):
        """ The list of available triggers.

        :type: list[str]
        """
        return self.get_attr_set('trigger')

    @property
    def trigger(self):
        """ LED trigger.

        A trigger is a kernel based source of led events. Triggers can either be simple or
        complex. A simple trigger isn't configurable and is designed to slot into
        existing subsystems with minimal additional code. Examples are the `ide-disk` and
        `nand-disk` triggers.

        Complex triggers whilst available to all LEDs have LED specific
        parameters and work on a per LED basis. The `timer` trigger is an example.
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` and `off` time can
        be specified via `delay_{on,off}` attributes in milliseconds.
        You can change the brightness value of a LED independently of the timer
        trigger. However, if you set the brightness value to 0 it will
        also disable the `timer` trigger.

        :type: str
        """
        return self.get_attr_string('trigger')

    @trigger.setter
    def trigger(self, value):
        self.set_attr_string('trigger', value)

    @property
    def delay_on(self):
        """ The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.

        :type: int
        """
        return self.get_attr_int('delay_on')

    @delay_on.setter
    def delay_on(self, value):
        self.set_attr_int('delay_on', value)

    @property
    def delay_off(self):
        """ The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.

        :type: int
        """
        return self.get_attr_int('delay_off')

    @delay_off.setter
    def delay_off(self, value):
        self.set_attr_int('delay_off', value)

    @property
    def brightness_pct(self):
        """ LED brightness in fraction of max_brightness (from 0.0 to -1.0).

        :type: float
        """
        return float(self.brightness) / self.max_brightness

    @brightness_pct.setter
    def brightness_pct(self, value):
        self.brightness = value * self.max_brightness


#: Used internally to define the buttons available on the target
ButtonDefinition = namedtuple('ButtonDefinition', 'input_path mask')


class ButtonManagerBase(object):
    """ Abstract root class providing the services for interacting with
    buttons available on the target.

    It is used for brick buttons, but also for remote command ones.

    To relieve the application from taking care of the buttons periodic
    polling, a threaded scanner is available, which will take care of this
    and process the state changes. See :py:meth:`start_scanner`,
    :py:meth:`stop_scanner`  and :py:meth:`_scan_buttons` methods for details.
    """
    _state = set()
    _scanner = None
    _stop_scan = False

    @property
    def buttons_pressed(self):
        """ The list of buttons currently pressed.

        It is returned as a set containing their names.

        :type: set[str]
        """
        raise NotImplementedError()

    @staticmethod
    def on_change(changed_buttons):
        """ This handler is called by `process()` whenever state of any button has
        changed since last `process()` call. It can be overridden by application code
        to attach a specific behavior to the buttons.

        Examples:

            >>> def handler(changed_buttons):
            >>>     ...
            >>>
            >>> mgr = ButtonManagerBase()
            >>> mgr.on_change = handler

        Args:
            changed_buttons (list[tuple[str, bool]]): the list of
                tuples of changed button names and their states.
        """
        pass

    def any(self):
        """ Returns `True` if any button is pressed.
        """
        return bool(self.buttons_pressed)

    def check_buttons(self, buttons=None):
        """ Tests if all listed buttons are currently pressed.

        Args:
            buttons (set[str]): the list of expected pressed buttons
        """
        return self.buttons_pressed == set(buttons or [])

    def process(self):
        """ Checks for currently pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.

        There are two kinds of handlers which can be defined:

            - individual button handlers, connected to `on_<button_name>` slots
            - global change handler, connected to `on_change` slot

        Individual button handlers are called first, and then the global change handler.

        Individual handlers are defined as empty methods in concrete classes implemented
        a given platform. See :py:class:`ev3.Button` and :py:class:`brickpi.Button` for
        examples.
        """
        new_state = self.buttons_pressed
        old_state = self._state
        self._state = new_state

        state_diff = new_state.symmetric_difference(old_state)
        for button in state_diff:
            try:
                # invoke the button handler if defined
                handler = getattr(self, 'on_' + button)
                handler(button in new_state)
            except AttributeError:
                pass

        if state_diff and self.on_change:
            self.on_change([(button, button in new_state) for button in state_diff])

    def start_scanner(self):
        """ Starts the automatic buttons scanner if not yet active.

        The polling loop runs in a separate thread.

        Calling this method while the scanner is running does nothing.

        Returns:
            bool: True is the scanner has been started, False if it was already running
        """
        if not self._scanner:
            self._scanner = threading.Thread(target=self._scan_buttons)
            self._scanner.start()
            return True
        else:
            return False

    def stop_scanner(self):
        """ Stops the automatic buttons scanner if active.

        Calling this method while the scanner is not running does nothing.

        Returns:
            bool: True is the scanner has been stopped, False if it was not running
        """
        if self._scanner:
            self._stop_scan = True
            self._scanner.join(10)
            self._scanner = None
            return True
        else:
            return False

    def _scan_buttons(self):
        """ The threading buttons polling loop.

        It takes care of processing the buttons every 0.1s until the stop flag
        has been set by a :py:meth:`stop_scan` call.

        .. Important::

            The callbacks attached to the various state change events will be executed
            in the context of the **scanner thread**, and not the main one. This must be taken in
            account if using resources which are also manipulated in the main thread (or other
            ones), protecting the accesses with the appropriate synchronisation mechanisms
            (semaphore, locks,...)
        """
        self._stop_scan = False
        while not self._stop_scan:
            self.process()
            time.sleep(0.1)


class ButtonManagerEVIO(ButtonManagerBase):
    """ Specialized button manager working with event interface
    and may be adapted to platform specific implementations.

    This implementation depends on the availability of the EVIOCGKEY ioctl
    to be able to read the button state buffer. See Linux kernel source
    in /include/uapi/linux/input.h for details.
    """

    KEY_MAX = 0x2FF
    KEY_BUF_LEN = int((KEY_MAX + 7) / 8)
    EVIOCGKEY = (2 << (14 + 8 + 8) | KEY_BUF_LEN << (8 + 8) | ord('E') << 8 | 0x18)

    _buttons = {}

    def __init__(self):
        self._file_cache = FileCache()
        self._buffer_cache = {}
        for btn_props in self._buttons.itervalues():
            self._button_file(btn_props.input_path)
            self._button_buffer(btn_props.input_path)

    def _button_file(self, name):
        return self._file_cache.file_handle(name)

    def _button_buffer(self, name):
        if name not in self._buffer_cache:
            self._buffer_cache[name] = array.array('B', [0] * self.KEY_BUF_LEN)
        return self._buffer_cache[name]

    @property
    def buttons_pressed(self):
        """ The names of pressed buttons.

        :type: set[str]
        """
        for b in self._buffer_cache:
            fcntl.ioctl(self._button_file(b), self.EVIOCGKEY, self._buffer_cache[b])

        pressed = set()
        for btn_name, btn_props in self._buttons.items():
            buf = self._buffer_cache[btn_props.input_path]
            bit = btn_props.mask
            if not bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed.add(btn_name)
        return pressed


class PowerSupply(Device):
    """ A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'

    @property
    def measured_current(self):
        """ The measured current that the battery is supplying (in microamps)

        :type: int
        """
        return self.get_attr_int('current_now')

    @property
    def measured_voltage(self):
        """ The measured voltage that the battery is supplying (in microvolts)

        :type: int
        """
        return self.get_attr_int('voltage_now')

    @property
    def max_voltage(self):
        """ The maximum voltage of the battery (in microvolts)

        :type: int
        """
        return self.get_attr_int('voltage_max_design')

    @property
    def min_voltage(self):
        """ The minimum voltage of the battery (in microvolts)

        :type: int
        """
        return self.get_attr_int('voltage_min_design')

    @property
    def technology(self):
        """ The power supply technology (e.g. `Li-ion`).

        :type: str
        """
        return self.get_attr_string('technology')

    @property
    def type(self):
        """ The type of power supply (e.g. `battery`).

        :type: str
        """
        return self.get_attr_string('type')

    @property
    def measured_amps(self):
        """ The measured current that the battery is supplying (in amps)

        :type: float
        """
        return self.measured_current / 1e6

    @property
    def measured_volts(self):
        """ The measured voltage that the battery is supplying (in volts)

        :type: float
        """
        return self.measured_voltage / 1e6


class LegoPort(PluggedDevice):
    """
    The `lego_port` sysclass provides an interface for working with input and
    output ports that are compatible with LEGO MINDSTORMS RCX/NXT/EV3, LEGO
    WeDo and LEGO Power Functions sensors and motors. Supported devices include
    the LEGO MINDSTORMS EV3 Intelligent Brick, the LEGO WeDo USB hub and
    various sensor multiplexers from 3rd party manufacturers.

    Some types of ports may have multiple modes of operation. For example, the
    input ports on the EV3 brick can communicate with sensors using UART, I2C
    or analog validate signals - but not all at the same time. Therefore there
    are multiple modes available to connect to the different types of sensors.

    In most cases, ports are able to automatically detect what type of sensor
    or motor is connected. In some cases though, this must be manually specified
    using the `mode` and `set_device` attributes. The `mode` attribute affects
    how the port communicates with the connected device. For example the input
    ports on the EV3 brick can communicate using UART, I2C or analog voltages,
    but not all at the same time, so the mode must be set to the one that is
    appropriate for the connected sensor. The `set_device` attribute is used to
    specify the exact type of sensor that is connected. Note: the mode must be
    correctly set before setting the sensor type.

    Ports can be found at `/sys/class/lego-port/port<N>` where `<N>` is
    incremented each time a new port is registered. Note: The number is not
    related to the actual port at all - use the `port_name` attribute to find
    a specific port.
    """

    SYSTEM_CLASS_NAME = 'lego_port'

    @property
    def modes(self):
        """ The list of the available modes of the port.

        :type: list[str]
        """
        return self.get_attr_set('modes')

    @property
    def mode(self):
        """ The port mode.

        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.

        :type: str
        """
        return self.get_attr_string('mode')

    @mode.setter
    def mode(self, value):
        self.set_attr_string('mode', value)

    @property
    def set_device(self):
        """ For modes that support it, writing the name of a driver will cause a new
        device to be registered for that driver and attached to this port. For
        example, since NXT/Analog sensors cannot be auto-detected, you must use
        this attribute to load the correct driver.

        Returns -EOPNOTSUPP if setting a device is not supported.

        .. important:: This is a write-only property

        :type: str
        """
        raise Exception("set_device is a write-only property!")

    @set_device.setter
    def set_device(self, value):
        self.set_attr_string('set_device', value)

    @property
    def status(self):
        """ In most cases, the status is the same value as `mode`.

        In cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.

        :type: str
        """
        return self.get_attr_string('status')
