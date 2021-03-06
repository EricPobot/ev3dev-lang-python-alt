# -*- coding: utf-8 -*-

import ctypes
import fcntl
import mmap
import os
from struct import pack

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise ImportError('PIL (or Pillow) library is required for screen usage')


class FbMem(object):
    """ The framebuffer memory object.

    Made of:
        - the framebuffer file descriptor
        - the fix screen info struct
        - the var screen info struct
        - the mapped memory
    """

    # ------------------------------------------------------------------
    # The code is adapted from
    # https://github.com/LinkCareServices/cairotft/blob/master/cairotft/linuxfb.py
    #
    # The original code came with the following license:
    # ------------------------------------------------------------------
    # Copyright (c) 2012 Kurichan
    #
    # This program is free software. It comes without any warranty, to
    # the extent permitted by applicable law. You can redistribute it
    # and/or modify it under the terms of the Do What The Fuck You Want
    # To Public License, Version 2, as published by Sam Hocevar. See
    # http://sam.zoy.org/wtfpl/COPYING for more details.
    # ------------------------------------------------------------------

    __slots__ = ('fid', 'fix_info', 'var_info', 'mmap')

    FBIOGET_VSCREENINFO = 0x4600
    FBIOGET_FSCREENINFO = 0x4602

    FB_VISUAL_MONO01 = 0
    FB_VISUAL_MONO10 = 1

    class FixScreenInfo(ctypes.Structure):
        """ The fb_fix_screeninfo from fb.h."""

        _fields_ = [
            ('id_name', ctypes.c_char * 16),
            ('smem_start', ctypes.c_ulong),
            ('smem_len', ctypes.c_uint32),
            ('type', ctypes.c_uint32),
            ('type_aux', ctypes.c_uint32),
            ('visual', ctypes.c_uint32),
            ('xpanstep', ctypes.c_uint16),
            ('ypanstep', ctypes.c_uint16),
            ('ywrapstep', ctypes.c_uint16),
            ('line_length', ctypes.c_uint32),
            ('mmio_start', ctypes.c_ulong),
            ('mmio_len', ctypes.c_uint32),
            ('accel', ctypes.c_uint32),
            ('reserved', ctypes.c_uint16 * 3),
        ]

    class VarScreenInfo(ctypes.Structure):

        class FbBitField(ctypes.Structure):
            """The fb_bitfield struct from fb.h."""

            _fields_ = [
                ('offset', ctypes.c_uint32),
                ('length', ctypes.c_uint32),
                ('msb_right', ctypes.c_uint32),
            ]

        """The fb_var_screeninfo struct from fb.h."""

        _fields_ = [
            ('xres', ctypes.c_uint32),
            ('yres', ctypes.c_uint32),
            ('xres_virtual', ctypes.c_uint32),
            ('yres_virtual', ctypes.c_uint32),
            ('xoffset', ctypes.c_uint32),
            ('yoffset', ctypes.c_uint32),

            ('bits_per_pixel', ctypes.c_uint32),
            ('grayscale', ctypes.c_uint32),

            ('red', FbBitField),
            ('green', FbBitField),
            ('blue', FbBitField),
            ('transp', FbBitField),
        ]

    def __init__(self, fbdev=None):
        """Create the FbMem framebuffer memory object."""
        fid = FbMem._open_fbdev(fbdev)
        fix_info = FbMem._get_fix_info(fid)
        fbmmap = FbMem._map_fb_memory(fid, fix_info)
        self.fid = fid
        self.fix_info = fix_info
        self.var_info = FbMem._get_var_info(fid)
        self.mmap = fbmmap

    def __del__(self):
        """Close the FbMem framebuffer memory object."""
        self.mmap.close()
        FbMem._close_fbdev(self.fid)

    @staticmethod
    def _open_fbdev(fbdev=None):
        """Return the framebuffer file descriptor.

        Try to use the FRAMEBUFFER
        environment variable if fbdev is not given. Use '/dev/fb0' by
        default.
        """
        dev = fbdev or os.getenv('FRAMEBUFFER', '/dev/fb0')
        fbfid = os.open(dev, os.O_RDWR)
        return fbfid

    @staticmethod
    def _close_fbdev(fbfid):
        """Close the framebuffer file descriptor."""
        os.close(fbfid)

    @staticmethod
    def _get_fix_info(fbfid):
        """Return the fix screen info from the framebuffer file descriptor."""
        fix_info = FbMem.FixScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_FSCREENINFO, fix_info)
        return fix_info

    @staticmethod
    def _get_var_info(fbfid):
        """Return the var screen info from the framebuffer file descriptor."""
        var_info = FbMem.VarScreenInfo()
        fcntl.ioctl(fbfid, FbMem.FBIOGET_VSCREENINFO, var_info)
        return var_info

    @staticmethod
    def _map_fb_memory(fbfid, fix_info):
        """Map the framebuffer memory."""
        return mmap.mmap(
            fbfid,
            fix_info.smem_len,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=0
        )


class Screen(FbMem):
    """ A convenience wrapper for the FbMem class.

    Provides drawing functions from the python imaging library (PIL).
    """

    def __init__(self):
        FbMem.__init__(self)

        self._img = Image.new(
                self.var_info.bits_per_pixel == 1 and "1" or "RGB",
                (self.fix_info.line_length * 8 / self.var_info.bits_per_pixel, self.yres),
                "white")

        self._draw = ImageDraw.Draw(self._img)

    @property
    def xres(self):
        """ Horizontal screen resolution
        """
        return self.var_info.xres

    @property
    def yres(self):
        """ Vertical screen resolution
        """
        return self.var_info.yres

    @property
    def shape(self):
        """ Dimensions of the screen.

        :type: tuple[int, int]
        """
        return self.xres, self.yres

    @property
    def draw(self):
        """ Returns a handle to PIL.ImageDraw.Draw class associated with the screen.

        Example:

            >>> screen.draw.rectangle((10,10,60,20), fill='black')
        """
        return self._draw

    @property
    def img(self):
        """ The handle to the PIL.Image class associated with the screen.

        Example:

            >>> screen.img.paste(tux, (10,10,60,20))
        """
        return self._img

    def clear(self):
        """ Clears the screen
        """
        self._draw.rectangle(((0, 0), self.shape), fill="white")

    def _color565(self, r, g, b):
        """ Convert red, green, blue components to a 16-bit 565 RGB value. Components
        should be values 0 to 255.
        """
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def _img_to_rgb565_bytes(self):
        pixels = [self._color565(r, g, b) for (r, g, b) in self._img.getdata()]
        return pack('H' * len(pixels), *pixels)

    def update(self):
        """ Applies pending changes to the screen.

        Nothing will be drawn on the screen until this function is called.
        """
        if self.var_info.bits_per_pixel == 1:
            self.mmap[:] = self._img.tobytes("raw", "1;IR")
        elif self.var_info.bits_per_pixel == 16:
            self.mmap[:] = self._img_to_rgb565_bytes()
        else:
            raise Exception("Not supported")

    @staticmethod
    def hide_cursor():
        """ Hides the text cursor.
        """
        print("\033[?25l")

    @staticmethod
    def show_cursor():
        """ Shown the text cursor.
        """
        print("\033[?25h")
