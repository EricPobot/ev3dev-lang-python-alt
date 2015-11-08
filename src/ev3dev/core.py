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
from subprocess import Popen

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
        if not os.path.isfile(path):
            raise ValueError('path not found')

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
    """

    DEVICE_ROOT_PATH = '/sys/class'

    _DEVICE_INDEX = re.compile(r'^.*(?P<idx>\d+)$')

    def __init__(self, class_name, name='*', **kwargs):
        """Spin through the Linux sysfs class for the device type and find
        a device that matches the provided name and attributes (if any).

        Args:
            class_name (str): class name of the device, a subdirectory of /sys/class.
                For example, 'tacho-motor'.
            name (str): pattern that device name should match.
                For example, 'sensor*' or 'motor*'. Default value: '*'.
            keyword arguments: used for matching the corresponding device
                attributes. For example, port_name='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Examples:

            >>> d = Device('tacho-motor', port_name='outA')
            >>> s = Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected successfully, the `connected` attribute is set to True.
        """

        classpath = os.path.join(Device.DEVICE_ROOT_PATH, class_name)

        for file_name in os.listdir(classpath):
            if fnmatch.fnmatch(file_name, name):
                self._path = os.path.join(classpath, file_name)
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
        """Internal device attribute getter"""
        return self._attribute_cache.read(attribute)

    def _set_attribute(self, attribute, value):
        """Internal device attribute setter"""
        self._attribute_cache.write(attribute, value)

    # TODO do we need get/set_attr_xxx methods in Python ?
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


class Led(Device):

    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


# ~autogen
# ~autogen generic-get-set classes.led>currentClass

    @property
    def max_brightness(self):
        """
        Returns the maximum allowable brightness value.
        """
        return self.get_attr_int('max_brightness')

    @property
    def brightness(self):
        """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """
        return self.get_attr_int('brightness')

    @brightness.setter
    def brightness(self, value):
        self.set_attr_int('brightness', value)

    @property
    def triggers(self):
        """
        Returns a list of available triggers.
        """
        return self.get_attr_set('trigger')

    @property
    def trigger(self):
        """
        Sets the led trigger. A trigger
        is a kernel based source of led events. Triggers can either be simple or
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
        """
        return self.get_attr_from_set('trigger')

    @trigger.setter
    def trigger(self, value):
        self.set_attr_string('trigger', value)

    @property
    def delay_on(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """
        return self.get_attr_int('delay_on')

    @delay_on.setter
    def delay_on(self, value):
        self.set_attr_int('delay_on', value)

    @property
    def delay_off(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """
        return self.get_attr_int('delay_off')

    @delay_off.setter
    def delay_off(self, value):
        self.set_attr_int('delay_off', value)


# ~autogen

    @property
    def brightness_pct(self):
        """
        Returns led brightness as a fraction of max_brightness
        """
        return float(self.brightness) / self.max_brightness

    @brightness_pct.setter
    def brightness_pct(self, value):
        self.brightness = value * self.max_brightness


class ButtonBase(object):
    """
    Abstract button interface.
    """

    @staticmethod
    def on_change(changed_buttons):
        """
        This handler is called by `process()` whenever state of any button has
        changed since last `process()` call. `changed_buttons` is a list of
        tuples of changed button names and their states.
        """
        pass

    _state = set([])

    def any(self):
        """
        Checks if any button is pressed.
        """
        return bool(self.buttons_pressed)

    def check_buttons(self, buttons=[]):
        """
        Check if currently pressed buttons exactly match the given list.
        """
        return set(self.buttons_pressed) == set(buttons)

    def process(self):
        """
        Check for currenly pressed buttons. If the new state differs from the
        old state, call the appropriate button event handlers.
        """
        new_state = set(self.buttons_pressed)
        old_state = self._state
        self._state = new_state

        state_diff = new_state.symmetric_difference(old_state)
        for button in state_diff:
            handler = getattr(self, 'on_' + button)
            if handler is not None: handler(button in new_state)

        if self.on_change is not None and state_diff:
            self.on_change([(button, button in new_state) for button in state_diff])


class ButtonEVIO(ButtonBase):

    """
    Provides a generic button reading mechanism that works with event interface
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
        for b in self._buttons:
            self._button_file(self._buttons[b]['name'])
            self._button_buffer(self._buttons[b]['name'])

    def _button_file(self, name):
        return self._file_cache.file_handle(name)

    def _button_buffer(self, name):
        if name not in self._buffer_cache:
            self._buffer_cache[name] = array.array('B', [0] * self.KEY_BUF_LEN)
        return self._buffer_cache[name]

    @property
    def buttons_pressed(self):
        """
        Returns list of names of pressed buttons.
        """
        for b in self._buffer_cache:
            fcntl.ioctl(self._button_file(b), self.EVIOCGKEY, self._buffer_cache[b])

        pressed = []
        for k, v in self._buttons.items():
            buf = self._buffer_cache[v['name']]
            bit = v['value']
            if not bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed += [k]
        return pressed


class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)


    @property
    def measured_current(self):
        """
        The measured current that the battery is supplying (in microamps)
        """
        return self.get_attr_int('current_now')

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)
        """
        return self.get_attr_int('voltage_now')

    @property
    def max_voltage(self):
        """
        """
        return self.get_attr_int('voltage_max_design')

    @property
    def min_voltage(self):
        """
        """
        return self.get_attr_int('voltage_min_design')

    @property
    def technology(self):
        """
        """
        return self.get_attr_string('technology')

    @property
    def type(self):
        """
        """
        return self.get_attr_string('type')

    @property
    def measured_amps(self):
        """
        The measured current that the battery is supplying (in amps)
        """
        return self.measured_current / 1e6

    @property
    def measured_volts(self):
        """
        The measured voltage that the battery is supplying (in volts)
        """
        return self.measured_voltage / 1e6


class LegoPort(Device):

    """
    The `lego-port` class provides an interface for working with input and
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
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

    @property
    def driver_name(self):
        """
        Returns the name of the driver that loaded this device. You can find the
        complete list of drivers in the [list of port drivers].
        """
        return self.get_attr_string('driver_name')

    @property
    def modes(self):
        """
        Returns a list of the available modes of the port.
        """
        return self.get_attr_set('modes')

    @property
    def mode(self):
        """
        Reading returns the currently selected mode. Writing sets the mode.
        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.
        """
        return self.get_attr_string('mode')

    @mode.setter
    def mode(self, value):
        self.set_attr_string('mode', value)

    @property
    def port_name(self):
        """
        Returns the name of the port. See individual driver documentation for
        the name that will be returned.
        """
        return self.get_attr_string('port_name')

    @property
    def set_device(self):
        """
        For modes that support it, writing the name of a driver will cause a new
        device to be registered for that driver and attached to this port. For
        example, since NXT/Analog sensors cannot be auto-detected, you must use
        this attribute to load the correct driver. Returns -EOPNOTSUPP if setting a
        device is not supported.
        """
        raise Exception("set_device is a write-only property!")

    @set_device.setter
    def set_device(self, value):
        self.set_attr_string('set_device', value)

    @property
    def status(self):
        """
        In most cases, reading status will return the same value as `mode`. In
        cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.
        """
        return self.get_attr_string('status')


class Sound:
    """
    Sound-related functions. The class has only static methods and is not
    intended for instantiation. It can beep, play wav files, or convert text to
    speech.

    Note that all methods of the class spawn system processes and return
    subprocess.Popen objects. The methods are asynchronous (they return
    immediately after child process was spawned, without waiting for its
    completion), but you can call wait() on the returned result.

    Examples::

        # Play 'bark.wav', return immediately:
        Sound.play('bark.wav')

        # Introduce yourself, wait for completion:
        Sound.speak('Hello, I am Robot').wait()
    """

    @staticmethod
    def beep(args=''):
        """
        Call beep command with the provided arguments (if any).
        See `beep man page`_ and google 'linux beep music' for inspiration.

        .. _`beep man page`: http://manpages.debian.org/cgi-bin/man.cgi?query=beep
        """
        with open(os.devnull, 'w') as n:
            return Popen('/usr/bin/beep %s' % args, stdout=n, shell=True)

    @staticmethod
    def tone(*args):
        """
        tone(tone_sequence):

        Play tone sequence. The tone_sequence parameter is a list of tuples,
        where each tuple contains up to three numbers. The first number is
        frequency in Hz, the second is duration in milliseconds, and the third
        is delay in milliseconds between this and the next tone in the
        sequence.

        Here is a cheerful example::

            Sound.tone([
                (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
                (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
                (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
                (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
                (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
                (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
                (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
                (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
                (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
                (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
                (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
                (466.16, 25, 100), (587.32, 700, 100), (784, 350, 100), (392, 250, 100),
                (392, 25, 100), (784, 350, 100), (739.98, 250, 100), (698.46, 25, 100),
                (659.26, 25, 100), (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200),
                (554.36, 350, 100), (523.25, 250, 100), (493.88, 25, 100),
                (466.16, 25, 100), (440, 25, 100), (466.16, 50, 400), (311.13, 25, 200),
                (392, 350, 100), (311.13, 250, 100), (466.16, 25, 100),
                (392.00, 300, 150), (311.13, 250, 100), (466.16, 25, 100), (392, 700)
                ]).wait()

        tone(frequency, duration):

        Play single tone of given frequency (Hz) and duration (milliseconds).
        """
        def play_tone_sequence(tone_sequence):
            def beep_args(frequency=None, duration=None, delay=None):
                args = '-n '
                if frequency is not None: args += '-f %s ' % frequency
                if duration  is not None: args += '-l %s ' % duration
                if delay     is not None: args += '-d %s ' % delay

                return args

            return Sound.beep(' '.join([beep_args(*t) for t in tone_sequence]))

        if len(args) == 1:
            return play_tone_sequence(args[0])
        elif len(args) == 2:
            return play_tone_sequence([(args[0], args[1])])
        else:
            raise Exception("Unsupported number of parameters in Sound.tone()")

    @staticmethod
    def play(wav_file):
        """
        Play wav file.
        """
        with open(os.devnull, 'w') as n:
            return Popen('/usr/bin/aplay -q "%s"' % wav_file, stdout=n, shell=True)

    @staticmethod
    def speak(text):
        """
        Speak the given text aloud.
        """
        with open(os.devnull, 'w') as n:
            return Popen('/usr/bin/espeak -a 200 --stdout "%s" | /usr/bin/aplay -q' % text, stdout=n, shell=True)
