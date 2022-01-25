# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT# LED bubble display widget

# based on the HP QDSP-6064 4-Digit Micro 7 Segment Numeric Indicator
# 2021-12-12 v1.0

import displayio
import vectorio
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect

# 8-bit to 7 segment
#  bits: dp g f e d c b a
NUMBERS = {
    "0": 0b00111111,  # 0
    "1": 0b00000110,  # 1
    "2": 0b01011011,  # 2
    "3": 0b01001111,  # 3
    "4": 0b01100110,  # 4
    "5": 0b01101101,  # 5
    "6": 0b01111101,  # 6
    "7": 0b00000111,  # 7
    "8": 0b01111111,  # 8
    "9": 0b01101111,  # 9
    "a": 0b01110111,  # a
    "b": 0b01111100,  # b
    "c": 0b00111001,  # C
    "d": 0b01011110,  # d
    "e": 0b01111001,  # E
    "f": 0b01110001,  # F
    "-": 0b01000000,  # -
    ".": 0b10000000,  # .
    " ": 0b00000000,  # <space>
    "x": 0b00001000,  # _ (replace x with underscore for hexadecimal text)
}


class Colors:
    # Define a few colors (https://en.wikipedia.org/wiki/Web_colors)
    BLACK = 0x000000
    RED = 0xFF0000
    RED_PKG = 0x100808
    RED_BKG = 0x0D0000
    RED_LENS = 0x601010
    WHITE = 0xFFFFFF


class BubbleDisplay(displayio.Group):
    def __init__(
        self, units=1, digits=4, mode="Normal", center=(0.5, 0.5), size=1,
        display_size=(None, None),
    ):
        """Instantiate the multi-digit 7-segment numeric end-stackable
        LED display graphic object for DisplayIO devices. Builds a hierachical
        DisplayIO group consisting of chip, digits, and digit segments.

        This widget is based on the HP-QDSP-6064 4-digit and the HP-35
        calculator's HP-5802-7433 3-digit 7-segment numeric end-stackable
        LED displays.

        This widget class displays decimal numeric values as well
        as alphanumeric strings (with a limited character set). Decimal values
        are right-justified with the decimal point placed within the 'ones'
        digit or between digits as specified by the mode parameter. Strings are
        left-justified. Alpha string characters are limited to upper or lower
        case 'a', 'b', 'c', 'd', 'e', 'f', 'x', '.', '-', and the space
        character.

        Display size in pixels is specified as an integer tuple. If the
        display_size tuple is not specified and a built-in display is listed in
        the board class, the display_size tuple will be equal to the integral
        built-in display width and height.

        :param integer units: The number of end-stacked widget units. Defaults
        to 1 widget.
        :param integer digits: The number of digits per display
        cluster (unit) ranging from 1 to 5 digits. Defaults to 4 digits per unit.
        :param string mode: The decimal point display mode. The default 'Normal'
        mode places the decimal point within the 'ones' digit; in 'HP-35' mode,
        the decimal point is place in a separate digit between the 'ones' and
        'one-tenth' digits.
        :param float center: The widget center x,y tuple in normalized display
        units. Defaults to (0.5, 0.5).
        :param float size: The widget size factor relative to the display's
        smaller axis. Defaults to 0.5.
        :param integer display_size: The host display's integer width and
        height tuple expressed in pixels. If (None, None) and the host includes
        an integral display, the tuple value is set to (board.DISPLAY.width,
        board.DISPLAY.height)."""

        # Determine default display size in pixels
        if None in display_size:
            import board

            if "DISPLAY" in dir(board):
                self.WIDTH = board.DISPLAY.width
                self.HEIGHT = board.DISPLAY.height
            else:
                raise ValueError("No integral display. Specify display size.")
        else:
            self.WIDTH = display_size[0]
            self.HEIGHT = display_size[1]

        # Define object center in normalized display and pixel coordinates
        self._center_norm = center
        self._center = self.display_to_pixel(self._center_norm[0], self._center_norm[1])
        self._size = size
        self._mode = mode
        self._units = max(0, units)
        self._num_digits = min(5, max(1, digits))

        # Create displayio group layers
        cluster = displayio.Group()
        self._digits = displayio.Group()

        red_bkg_palette = displayio.Palette(1)
        red_bkg_palette[0] = Colors.RED_BKG
        dip_pkg_palette = displayio.Palette(1)
        dip_pkg_palette[0] = Colors.RED_PKG
        blk_palette = displayio.Palette(1)
        blk_palette[0] = Colors.BLACK

        widget_upper_left = (
            self._center[0]
            - self.cart_dist_to_pixel(0.250 / 2 * self._units, self._size),
            self._center[1] - self.cart_dist_to_pixel(0.100 / 2, self._size),
        )

        for chip in range(0, self._units):
            upper_left_corner = (
                widget_upper_left[0]
                + (self.cart_dist_to_pixel(0.250 * chip, self._size)),
                widget_upper_left[1],
            )
            dip_pkg = vectorio.Rectangle(
                pixel_shader=dip_pkg_palette,
                x=upper_left_corner[0],
                y=upper_left_corner[1],
                width=self.cart_dist_to_pixel(0.250, self._size),
                height=self.cart_dist_to_pixel(0.100, self._size),
            )
            cluster.append(dip_pkg)

            dip_index = vectorio.Rectangle(
                pixel_shader=blk_palette,
                x=upper_left_corner[0],
                y=self.cart_dist_to_pixel(0.096, self._size) + upper_left_corner[1],
                width=self.cart_dist_to_pixel(0.010, self._size),
                height=self.cart_dist_to_pixel(0.010, self._size),
            )
            cluster.append(dip_index)

            a1 = (
                self.cart_dist_to_pixel(0.021, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.025, self._size) + upper_left_corner[1],
            )
            b1 = (
                self.cart_dist_to_pixel(0.046, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.025, self._size) + upper_left_corner[1],
            )
            c1 = (
                self.cart_dist_to_pixel(0.042, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.050, self._size) + upper_left_corner[1],
            )
            d1 = (
                self.cart_dist_to_pixel(0.038, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.075, self._size) + upper_left_corner[1],
            )
            e1 = (
                self.cart_dist_to_pixel(0.013, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.075, self._size) + upper_left_corner[1],
            )
            f1 = (
                self.cart_dist_to_pixel(0.017, self._size) + upper_left_corner[0],
                self.cart_dist_to_pixel(0.050, self._size) + upper_left_corner[1],
            )
            if mode == "HP-35":
                dp = (
                    self.cart_dist_to_pixel(0.029, self._size) + upper_left_corner[0],
                    self.cart_dist_to_pixel(0.065, self._size) + upper_left_corner[1],
                    )
            else:
                dp = (
                    self.cart_dist_to_pixel(0.046, self._size) + upper_left_corner[0],
                    self.cart_dist_to_pixel(0.075, self._size) + upper_left_corner[1],
                    )

            dp_size = self.cart_dist_to_pixel(0.008, self._size)

            step_norm = 0.250 / self._num_digits
            step_offset = self.cart_dist_to_pixel(0.09374 - ((0.25 - step_norm) / 2), self._size)

            for i in range(0, self._num_digits):
                step = i * self.cart_dist_to_pixel(step_norm, self._size)
                lens = RoundRect(
                    upper_left_corner[0] + step,
                    upper_left_corner[1],
                    self.cart_dist_to_pixel(step_norm, self._size),
                    self.cart_dist_to_pixel(0.100, self._size),
                    self.cart_dist_to_pixel(0.029, self._size),
                    fill=Colors.RED_BKG,
                    outline=Colors.RED_LENS,
                )
                cluster.append(lens)

                seg_a = Line(
                    a1[0] + step + step_offset,
                    a1[1],
                    b1[0] + step + step_offset,
                    b1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_a)

                seg_b = Line(
                    b1[0] + step + step_offset,
                    b1[1],
                    c1[0] + step + step_offset,
                    c1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_b)

                seg_c = Line(
                    c1[0] + step + step_offset,
                    c1[1],
                    d1[0] + step + step_offset,
                    d1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_c)

                seg_d = Line(
                    d1[0] + step + step_offset,
                    d1[1],
                    e1[0] + step + step_offset,
                    e1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_d)

                seg_e = Line(
                    e1[0] + step + step_offset,
                    e1[1],
                    f1[0] + step + step_offset,
                    f1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_e)

                seg_f = Line(
                    f1[0] + step + step_offset,
                    f1[1],
                    a1[0] + step + step_offset,
                    a1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_f)

                seg_g = Line(
                    f1[0] + step + step_offset,
                    f1[1],
                    c1[0] + step + step_offset,
                    c1[1],
                    color=Colors.RED_BKG,
                )
                self._digits.append(seg_g)

                seg_dp = Rect(
                    dp[0] + step + step_offset,
                    dp[1],
                    dp_size,
                    dp_size,
                    fill=Colors.RED_BKG,
                )
                self._digits.append(seg_dp)
        super().__init__()
        self.append(cluster)
        self.append(self._digits)
        return

    @property
    def units(self):
        """Number of units."""
        return self._units

    @property
    def units(self):
        """Number of digits per unit."""
        return self._digits

    @property
    def mode(self):
        """Bubble display display mode."""
        return self._mode

    @property
    def center(self):
        """Bubble display object center."""
        return self._center_norm

    @property
    def size(self):
        """Bubble display object size."""
        return self._size

    @property
    def display_size(self):
        """Display size in pixels."""
        return (self.WIDTH, self.HEIGHT)

    @property
    def value(self):
        """Currently displayed value."""
        return self._value

    @value.setter
    def value(self, value=None):
        self._show_value(value, self._mode)

    @property
    def text(self):
        """Currently displayed text."""
        return self._text

    @text.setter
    def text(self, text=""):
        self._show_text(text)

    # @property
    # def center(self, cluster=0):
    #    """Normalized display coordinates of the object center."""
    #    determine center of cluster specified by the cluster parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    # @centersetter
    # def center(self, cluster=0, x, y):
    #    """Set the normalized display coordinates of the object center."""
    #    procedure for setting all coordinates for a cluster
    #    as specified by the cluster parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    def _show_text(self, text=""):
        text = text[0 : self._units * self._num_digits]  # Truncate to left-most digits
        text = (" " * ((self._units * self._num_digits) - len(text))) + text

        for _digit in range(0, self._units * self._num_digits):
            if text[_digit] in NUMBERS:
                _decode = NUMBERS[text[_digit]]
            else:
                _decode = NUMBERS[" "]
            for _segment in range(0, 8):
                if _decode & pow(2, _segment):
                    self._digits[(_digit * 8) + _segment].color = Colors.RED
                    self._digits[(_digit * 8) + _segment].fill = Colors.RED
                else:
                    self._digits[(_digit * 8) + _segment].color = Colors.RED_BKG
                    self._digits[(_digit * 8) + _segment].fill = Colors.RED_BKG

    def _show_value(self, value=None, mode="Normal"):
        """ use mode='HP-35' for decimal point between digits """
        self._mode = mode
        if value == None:
            _display = ""
        else:
            _display = str(value)

        # if value string is larger than can be displayed, show dashes
        if len(_display) > self._units * self._num_digits:
            _display = "-" * self._units * self._num_digits
        else:
            _display = (" " * ((self._units * self._num_digits) - len(_display))) + _display

        # locate decimal point and remove from display string
        dp_digit = _display.find(".")
        if dp_digit > -1 and self._mode != "HP-35":
            _display = " " + _display[0:dp_digit] + _display[dp_digit + 1 :]

        self._show_text(_display)

        # clear all decimal points and plot the current point
        for digit in range(0, self._units * self._num_digits):
            self._digits[(digit * 8) + 7].fill = Colors.RED_BKG
        if dp_digit > -1:
            self._digits[(dp_digit * 8) + 7].fill = Colors.RED
        return

    def display_to_pixel(self, width_factor=0, height_factor=0, size=1.0):
        """Convert normalized display position input (0.0 to 1.0) to display
        pixel position."""
        return int(round(size * self.WIDTH * width_factor, 0)), int(
            round(size * self.HEIGHT * height_factor, 0)
        )

    def dial_to_pixel(self, dial_factor, center=(0, 0), radius=0):
        """Convert normalized dial_factor input (-1.0 to 1.0) to display pixel
        position on the circumference of the dial's circle with center
        (x,y pixels) and radius (pixels)."""
        rads = (-2 * pi) * (dial_factor)  # convert scale_factor to radians
        rads = rads + (pi / 2)  # rotate axis counterclockwise
        x = center[0] + int(cos(rads) * radius)
        y = center[1] - int(sin(rads) * radius)
        return x, y

    def cart_to_pixel(self, x, y, size=1.0):
        """Convert normalized cartesian position value (-0.5, to + 0.5) to display
        pixels."""
        min_axis = min(self.WIDTH, self.HEIGHT)
        x1 = int(round(min_axis * size * x, 0)) + self._center[0]
        y1 = self._center[1] - int(round(min_axis * size * y, 0))
        return x1, y1

    def cart_dist_to_pixel(self, distance=0, size=1.0):
        """Convert normalized cartesian distance value to display pixels."""
        min_axis = min(self.WIDTH, self.HEIGHT)
        return int(round(min_axis * size * distance, 0))
