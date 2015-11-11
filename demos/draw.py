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

""" Draw some stuff on the LCD.
"""

import time
import os

from ev3dev.display import Screen, Image

screen = Screen()
screen.hide_cursor()

w, h = screen.shape

for image_file in ('tux.png', 'pobot.png'):
    decal = Image.open(os.path.join(os.path.dirname(__file__), 'img', image_file))
    iw, ih = decal.size

    screen.draw.rectangle(
        ((0, 0), (w-1, h-1)),
        outline='black'
    )

    for i, dim in enumerate(zip('wh', (w, h))):
        label, value = dim
        s = "%s=%d" % (label, value)
        tw, th = screen.draw.textsize(s)
        screen.draw.text((w - tw - 1, 2 + i * th), s)

    screen.draw.arc((5, 5, 25, 25), 0, 360)
    screen.draw.arc((w - 25, h - 25, w - 5, h - 5), 0, 360)

    screen.img.paste(decal, ((w - iw)/2, (h - ih)/2, (w + iw)/2, (h + ih)/2), decal)

    screen.update()

    time.sleep(5)

    screen.clear()
