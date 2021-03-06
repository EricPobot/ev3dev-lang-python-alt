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

""" This module gathers definitions related to sound, including:

    - playing a beep
    - playing a note sequence (aka "song")
    - playing sound files
    - speaking

.. note::

    Writing songs played with tones is made simpler by using the the :py:meth:`Sound.play_song`
    which supports symbolic notes (e.g. ``A4``, ``D#3``, ``Gb5``) and durations (e.g. ``q``, ``h``).

    Refer to :py:attr:`NOTE_FREQUENCIES` and :py:attr:`NOTE_VALUES` for details
"""

import os
import subprocess


class Sound(object):
    """ Sound-related functions. The class has only static methods and is not
    intended for instantiation. It can beep, play wav files, or convert text to
    speech and speak them.

    Note that all methods of the class spawn system processes and return
    :py:class:`subprocess.Popen` objects. The methods are asynchronous (they return
    immediately after child process was spawned, without waiting for its
    completion), but you can call wait() on the returned result.

    Example::

        >>> # Play 'bark.wav', return immediately:
        >>> Sound.play('bark.wav')
        >>>
        >>> # Introduce yourself, wait for completion:
        >>> Sound.speak('Hello, I am Robot').wait()
    """

    @staticmethod
    def beep(args=''):
        """ Calls the beep command with the provided arguments (if any).
        See `beep man page`_ and google 'linux beep music' for inspiration.

        Args:
            args (str): arguments passed to the `beep` command

        Returns:
            subprocess.Popen: the spawn subprocess

        .. note::

            The :py:meth:`play_song` is more friendly for song playing, since the
            melody is defined with note names and symbolic durations.

        .. _`beep man page`: http://manpages.debian.org/cgi-bin/man.cgi?query=beep
        """
        with open(os.devnull, 'w') as n:
            return subprocess.Popen('/usr/bin/beep %s' % args, stdout=n, shell=True)

    @staticmethod
    def tone(*args):
        """ Plays a tone or a tones sequence.

        **Single tone play**

        Args:
            frequency (int): tone frequency (Hz)
            duration (int): tone duration (ms)

        Returns:
            :py:class:`subprocess.Popen`: the spawn subprocess

        Simple example::

            Sound.tone(440, 1000)

        **Song play**

        Args:
            notes (list[tuple[int,int,int]]): the song notes, as triplets containing
                the frequency (Hz), the duration (ms) and the delay (ms) between
                this note and the next one

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
        """
        def play_tone_sequence(tone_sequence):
            def beep_args(frequency=None, duration=None, delay=None):
                _args = ''
                if frequency is not None: _args += '-f %s ' % frequency
                if duration  is not None: _args += '-l %s ' % duration
                if delay     is not None: _args += '-D %s ' % delay

                return _args

            return Sound.beep(' -n '.join([beep_args(*t) for t in tone_sequence]))

        if len(args) == 1:
            return play_tone_sequence(args[0])
        elif len(args) == 2:
            return play_tone_sequence([(args[0], args[1])])
        else:
            raise Exception("Unsupported number of parameters in Sound.tone()")

    @staticmethod
    def play(wav_file):
        """ Plays a WAV file.

        Args:
            wav_file (str): the path of the WAV file
        Returns:
            subprocess.Popen: the spawn subprocess

        .. note::

            RSF LEGO sound files are supported by this method, so it is
            possible to use the ones included in the MINDSTORMS graphical environment.
        """
        return subprocess.Popen('/usr/bin/aplay "%s" > /dev/null 2>&1' % wav_file, shell=True)

    @staticmethod
    def play_song(song, tempo=120, delay=50):
        """ Plays a song provided as a list of tuples containing the note name and its
        value.

        Note names and values are defined by the :py:attr:`NOTES` and :py:attr:`NOTE_VALUES`
        dictionaries. The value can be suffixed by modifiers:

        - a *divider* introduced by a ``/`` to obtain triplets for instance
          (e.g. ``q/3`` for a triplet of eight note)
        - a *multiplier* introduced by ``*`` (e.g. ``*1.5`` is a dotted note).

        Shortcuts exist for common modifiers:

        - ``3`` produces a triplet member note. For instance `e3` gives a triplet of eight notes,
          i.e. 3 eight notes in the duration of a single quarter. You must ensure that 3 triplets
          notes are defined in sequence to match the count, otherwise the result will not be the
          expected one.
        - ``.`` produces a dotted note, i.e. which duration is one and a half the base one. Double dots
          are not currently supported.

        Example::

            >>> # A long time ago in a galaxy far,
            >>> # far away...
            >>> Sound.play_song((
            >>>     ('D4', 'e3'),      # intro anacrouse
            >>>     ('D4', 'e3'),
            >>>     ('D4', 'e3'),
            >>>     ('G4', 'h'),        # meas 1
            >>>     ('D5', 'h'),
            >>>     ('C5', 'e3'),      # meas 2
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 3
            >>>     ('B4', 'e3'),
            >>>     ('A4', 'e3'),
            >>>     ('G5', 'h'),
            >>>     ('D5', 'q'),
            >>>     ('C5', 'e3'),      # meas 4
            >>>     ('B4', 'e3'),
            >>>     ('C5', 'e3'),
            >>>     ('A4', 'h.'),
            >>> ))

        .. important::

            Only 4/4 signature songs are supported with respect to note durations.

        Args:
            song (iterable[tuple(str, str)]): the song
            tempo (int): the song tempo, given in quarters per minute
            delay (int): delay in ms between notes

        Returns:
            subprocess.Popen: the spawn subprocess
        """
        meas_duration = 60000 / tempo * 4

        def beep_args(note, value):
            """ Builds the arguments string for producing a beep matching
            the requested note and value.

            Args:
                note (str): the note note and octave
                value (str): the note value expression
            Returns:
                str: the arguments to be passed to the beep command
            """
            freq = NOTE_FREQUENCIES[note.upper()]
            if '/' in value:
                base, factor = value.split('/')
                duration = meas_duration * NOTE_VALUES[base] / float(factor)
            elif '*' in value:
                base, factor = value.split('*')
                duration = meas_duration * NOTE_VALUES[base] * float(factor)
            elif value.endswith('.'):
                base = value[:-1]
                duration = meas_duration * NOTE_VALUES[base] * 1.5
            elif value.endswith('3'):
                base = value[:-1]
                duration = meas_duration * NOTE_VALUES[base] * 2 / 3
            else:
                duration = meas_duration * NOTE_VALUES[value]

            return '-f %d -l %d -D %d' % (freq, duration, delay)

        return Sound.beep(' -n '.join(
            [beep_args(note, value) for note, value in song]
        ))

    @staticmethod
    def speak(text, amplitude=200, speed=150, voice='en', espeak_options=''):
        """ Speaks the given text aloud.

        Args:
            text (str): the text to speak
            amplitude (int): the voice amplitude. Default to 200
            speed (int): speech speed, in words per minute. Default to 175
            voice (str): the voice code (see content of `espeak-data/voices` for the list). Default to `en`
            espeak_options (str): additional espeak options, as described in documentation

        Returns:
            subprocess.Popen: the spawn subprocess
        """
        return subprocess.Popen(
            '/usr/bin/espeak -a %(amplitude)d -s %(speed)d -v %(voice)s %(opts)s --stdout "%(text)s" | '
            '/usr/bin/aplay > /dev/null 2>&1' %
            {
                'text': text,
                'speed': speed,
                'amplitude': amplitude,
                'voice': voice,
                'opts': espeak_options
            },
            shell=True)


def _make_scales(notes):
    res = dict()
    for note, freq in notes:
        freq = round(freq)
        for n in note.split('/'):
            res[n] = freq
    return res


#: Note frequencies.
#:
#: This dictionary gives the rounded frequency of a note specified by its
#: standard US abbreviation and its octave number (e.g. ``C3``).
#: Alterations use the ``#`` and ``b`` symbols, respectively for
#: *sharp* and *flat*, between the note code and the octave number (e.g. ``D#4``, ``Gb5``).
NOTE_FREQUENCIES = _make_scales((
    ('C0', 16.35), 
    ('C#0/Db0', 17.32),
    ('D0', 18.35),
    ('D#0/Eb0', 19.45),     # expanded in one entry per symbol by _make_scales
    ('E0', 20.60),
    ('F0', 21.83),
    ('F#0/Gb0', 23.12),
    ('G0', 24.50),
    ('G#0/Ab0', 25.96),
    ('A0', 27.50),
    ('A#0/Bb0', 29.14),
    ('B0', 30.87),
    ('C1', 32.70),
    ('C#1/Db1', 34.65),
    ('D1', 36.71),
    ('D#1/Eb1', 38.89),
    ('E1', 41.20),
    ('F1', 43.65),
    ('F#1/Gb1', 46.25),
    ('G1', 49.00),
    ('G#1/Ab1', 51.91),
    ('A1', 55.00),
    ('A#1/Bb1', 58.27),
    ('B1', 61.74),
    ('C2', 65.41),
    ('C#2/Db2', 69.30),
    ('D2', 73.42),
    ('D#2/Eb2', 77.78),
    ('E2', 82.41),
    ('F2', 87.31),
    ('F#2/Gb2', 92.50),
    ('G2', 98.00),
    ('G#2/Ab2', 103.83),
    ('A2', 110.00),
    ('A#2/Bb2', 116.54),
    ('B2', 123.47),
    ('C3', 130.81),
    ('C#3/Db3', 138.59),
    ('D3', 146.83),
    ('D#3/Eb3', 155.56),
    ('E3', 164.81),
    ('F3', 174.61),
    ('F#3/Gb3', 185.00),
    ('G3', 196.00),
    ('G#3/Ab3', 207.65),
    ('A3', 220.00),
    ('A#3/Bb3', 233.08),
    ('B3', 246.94),
    ('C4', 261.63),
    ('C#4/Db4', 277.18),
    ('D4', 293.66),
    ('D#4/Eb4', 311.13),
    ('E4', 329.63),
    ('F4', 349.23),
    ('F#4/Gb4', 369.99),
    ('G4', 392.00),
    ('G#4/Ab4', 415.30),
    ('A4', 440.00),
    ('A#4/Bb4', 466.16),
    ('B4', 493.88),
    ('C5', 523.25),
    ('C#5/Db5', 554.37),
    ('D5', 587.33),
    ('D#5/Eb5', 622.25),
    ('E5', 659.25),
    ('F5', 698.46),
    ('F#5/Gb5', 739.99),
    ('G5', 783.99),
    ('G#5/Ab5', 830.61),
    ('A5', 880.00),
    ('A#5/Bb5', 932.33),
    ('B5', 987.77),
    ('C6', 1046.50),
    ('C#6/Db6', 1108.73),
    ('D6', 1174.66),
    ('D#6/Eb6', 1244.51),
    ('E6', 1318.51),
    ('F6', 1396.91),
    ('F#6/Gb6', 1479.98),
    ('G6', 1567.98),
    ('G#6/Ab6', 1661.22),
    ('A6', 1760.00),
    ('A#6/Bb6', 1864.66),
    ('B6', 1975.53),
    ('C7', 2093.00),
    ('C#7/Db7', 2217.46),
    ('D7', 2349.32),
    ('D#7/Eb7', 2489.02),
    ('E7', 2637.02),
    ('F7', 2793.83),
    ('F#7/Gb7', 2959.96),
    ('G7', 3135.96),
    ('G#7/Ab7', 3322.44),
    ('A7', 3520.00),
    ('A#7/Bb7', 3729.31),
    ('B7', 3951.07),
    ('C8', 4186.01),
    ('C#8/Db8', 4434.92),
    ('D8', 4698.63),
    ('D#8/Eb8', 4978.03),
    ('E8', 5274.04),
    ('F8', 5587.65),
    ('F#8/Gb8', 5919.91),
    ('G8', 6271.93),
    ('G#8/Ab8', 6644.88),
    ('A8', 7040.00),
    ('A#8/Bb8', 7458.62),
    ('B8', 7902.13)
))

#: Common note values.
#:
#: See https://en.wikipedia.org/wiki/Note_value
#:
#: This dictionary provides the multiplier to be applied to de whole note duration
#: to obtain subdivisions, given the corresponding symbolic identifier:
#:
#:  = ===============================
#:  w whole note (UK: semibreve)
#:  h half note (UK: minim)
#:  q quarter note (UK: crotchet)
#:  e eight note (UK: quaver)
#:  s sixteenth note (UK: semiquaver)
#:  = ===============================
#:
#:
#: Triplets can be obtained by dividing the corresponding reference by 3.
#: For instance, the note value of a eight triplet will be ``NOTE_VALUE['e'] / 3``.
#: It is simpler however to user the ``3`` modifier of notes, as supported by the
#: :py:meth:`Sound.play_song` method.
NOTE_VALUES = {
    'w': 1.,
    'h': 1./2,
    'q': 1./4,
    'e': 1./8,
    's': 1./16,
}
