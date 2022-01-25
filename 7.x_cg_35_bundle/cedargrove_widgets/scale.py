# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# scale.py
# 2021-12-11 v2.5

import displayio
import vectorio
from math import pi, pow, sin, cos, sqrt
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_text.label import Label


class Colors:
    # Define a few colors (https://en.wikipedia.org/wiki/Web_colors)
    BLACK = 0x000000
    BLUE = 0x0000FF
    BLUE_DK = 0x000080
    CYAN = 0x00FFFF
    GRAY = 0x508080
    GREEN = 0x00FF00
    ORANGE = 0xFFA500
    RED = 0xFF0000
    WHITE = 0xFFFFFF


class Scale(displayio.Group):
    def __init__(
        self,
        num_hands=1,
        center=(0.50, 0.50),
        size=0.5,
        max_scale=100,
        display_size=(None, None),
    ):
        """Instantiate the scale graphic object for DisplayIO devices.
        The Scale class is a displayio group representing the scale widget.

        :param integer num_hands: The number of dial pointers.
        :param float center: The widget center x,y tuple in normalized display
        units. Defaults to (0.5, 0.5).
        :param float size: The widget size factor relative to the display's
        smaller axis. Defaults to 0.5.
        :param integer max_scale: The maximum scale integer value. Used for
        labeling the ten major dial hashmarks. Defaults to 100.
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

        if num_hands < 1 or num_hands > 2:
            raise ValueError("Number of hands must be 1 or 2.")
        self._num_hands = num_hands
        if size < 0 or size > 1:
            raise ValueError("Size must be in range of 0.0 to 1.0, inclusive.")
        self._size = size
        self._max_scale = max_scale
        self._hand1 = 0
        self._hand2 = 0
        self._alarm1 = None
        self._alarm2 = None

        # Define object center relative to normalized display and pixel coordinates
        self._center_norm = center
        self._center = self.display_to_pixel(self._center_norm[0], self._center_norm[1])

        if self._size < 0.50:
            self.FONT_0 = bitmap_font.load_font("/fonts/brutalist-6.bdf")
        else:
            self.FONT_0 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        scale_group = displayio.Group()
        self._hands_group = displayio.Group()
        pivot_group = displayio.Group()

        # Define dial radii layout
        self._outside_radius = self.cart_dist_to_pixel(0.5, self._size)
        major_radius = int(round(self._outside_radius * 0.88, 0))
        minor_radius = int(round(self._outside_radius * 0.93, 0))
        label_radius = int(round(self._outside_radius * 0.70, 0))
        point_radius = int(round(self._outside_radius * 0.06, 0))

        x1, y1 = self.cart_to_pixel(-0.49, -0.51, self._size)
        x2, y2 = self.cart_to_pixel(0.49, -0.51, self._size)
        base = Triangle(
            self._center[0],
            self._center[1],
            x1,
            y1,
            x2,
            y2,
            fill=Colors.GRAY,
            outline=Colors.BLACK,
        )
        scale_group.append(base)

        x, y = self.cart_to_pixel(-0.5, -0.5, self._size)
        foot = RoundRect(
            x,
            y,
            width=self.cart_dist_to_pixel(1.0, self._size),
            height=self.cart_dist_to_pixel(0.08, self._size),
            r=int(10 * self._size),
            fill=Colors.GRAY,
            outline=Colors.BLACK,
        )
        scale_group.append(foot)

        # Define moveable plate graphic
        self._plate_y = 0.65
        x, y = self.cart_to_pixel(-0.07, self._plate_y, self._size)
        self.riser = RoundRect(
            x,
            y,
            width=self.cart_dist_to_pixel(0.14, self._size),
            height=self.cart_dist_to_pixel(0.20, self._size),
            r=0,
            fill=Colors.GRAY,
            outline=Colors.BLACK,
        )
        scale_group.append(self.riser)

        x, y = self.cart_to_pixel(-0.5, self._plate_y, self._size)
        self.plate = RoundRect(
            x,
            y,
            width=self.cart_dist_to_pixel(1.0, self._size),
            height=self.cart_dist_to_pixel(0.08, self._size),
            r=int(10 * self._size),
            fill=Colors.GRAY,
            outline=Colors.BLACK,
        )
        scale_group.append(self.plate)

        # Define primary dial graphic
        dial = Circle(
            self._center[0],
            self._center[1],
            self._outside_radius,
            fill=Colors.BLUE_DK,
            outline=Colors.WHITE,
            stroke=1,
        )
        scale_group.append(dial)

        # Define hashmarks
        for i in range(0, self._max_scale, self._max_scale // 10):
            hash_value = Label(self.FONT_0, text=str(i), color=Colors.CYAN)
            hash_value.anchor_point = (0.5, 0.5)
            hash_value.anchored_position = self.dial_to_pixel(
                i / self._max_scale, center=self._center, radius=label_radius
            )
            scale_group.append(hash_value)

            # Major hashmarks
            x0, y0 = self.dial_to_pixel(
                i / self._max_scale, center=self._center, radius=major_radius
            )
            x1, y1 = self.dial_to_pixel(
                i / self._max_scale, center=self._center, radius=self._outside_radius
            )
            hashmark_a = Line(x0, y0, x1, y1, Colors.CYAN)
            scale_group.append(hashmark_a)

            # Minor hashmarks
            x0, y0 = self.dial_to_pixel(
                (i + self._max_scale / 20) / self._max_scale,
                center=self._center,
                radius=minor_radius,
            )
            x1, y1 = self.dial_to_pixel(
                (i + self._max_scale / 20) / self._max_scale,
                center=self._center,
                radius=self._outside_radius,
            )
            hashmark_b = Line(x0, y0, x1, y1, Colors.CYAN)
            scale_group.append(hashmark_b)

        # Define dial bezel
        bezel = Circle(
            self._center[0],
            self._center[1],
            self._outside_radius + 1,
            fill=None,
            outline=Colors.BLACK,
            stroke=1,
        )
        scale_group.append(bezel)

        # Define pointer 1
        self._base = self._outside_radius // 16
        self._hand1 = 0
        x0, y0 = self.dial_to_pixel(
            self._hand1, center=self._center, radius=self._outside_radius
        )
        x1, y1 = self.dial_to_pixel(
            self._hand1 - 0.25, center=self._center, radius=self._base
        )
        x2, y2 = self.dial_to_pixel(
            self._hand1 + 0.25, center=self._center, radius=self._base
        )
        pointer_1 = Triangle(
            x0,
            y0,
            x1,
            y1,
            x2,
            y2,
            fill=Colors.ORANGE,
            outline=Colors.ORANGE,
        )
        self._hands_group.append(pointer_1)

        # Define pointer 2
        if self._num_hands == 2:
            self._hand2 = 0
            hand2_fill = hand2_outline = None
            x0, y0 = self.dial_to_pixel(
                self._hand2, center=self._center, radius=self._outside_radius
            )
            x1, y1 = self.dial_to_pixel(
                self._hand2 - 0.25, center=self._center, radius=self._base
            )
            x2, y2 = self.dial_to_pixel(
                self._hand2 + 0.25, center=self._center, radius=self._base
            )
            pointer_2 = Triangle(
                x0,
                y0,
                x1,
                y1,
                x2,
                y2,
                fill=Colors.GREEN,
                outline=Colors.GREEN,
            )
            self._hands_group.append(pointer_2)

        # Define alarm points
        self._alarm1_palette = displayio.Palette(1)
        self._alarm1_palette[0] = Colors.ORANGE
        if self._alarm1 != None:
            x0, y0 = self.dial_to_pixel(
                self._alarm1, center=self._center, radius=self._outside_radius
            )
            self._alarm1_palette.make_opaque(0)
        else:
            x0 = y0 = 0
            self._alarm1_palette.make_transparent(0)

        self.alarm1_marker = vectorio.Circle(
            pixel_shader=self._alarm1_palette,
            radius=point_radius,
            x=x0,
            y=y0,
        )
        scale_group.append(self.alarm1_marker)

        self._alarm2_palette = displayio.Palette(1)
        self._alarm2_palette[0] = Colors.GREEN
        if self._alarm2 != None:
            x0, y0 = self.dial_to_pixel(
                self._alarm2, center=self._center, radius=self._outside_radius
            )
            self._alarm2_palette.make_opaque(0)
        else:
            x0 = y0 = 0
            self._alarm2_palette.make_transparent(0)

        self.alarm2_marker = vectorio.Circle(
            pixel_shader=self._alarm2_palette,
            radius=point_radius,
            x=x0,
            y=y0,
        )
        scale_group.append(self.alarm2_marker)

        # Define dial center piviot
        pivot_palette = displayio.Palette(1)
        pivot_palette[0] = Colors.CYAN
        x0, y0 = self.cart_to_pixel(0, 0, self._size)
        pivot = vectorio.Circle(
            pixel_shader=pivot_palette,
            radius=self._outside_radius // 14,
            x=x0,
            y=y0,
        )
        pivot_group.append(pivot)

        super().__init__()
        self.append(scale_group)
        self.append(self._hands_group)
        self.append(pivot_group)
        return

    @property
    def center(self):
        """Normalized display coordinates of object center."""
        return self._center_norm

    @property
    def size(self):
        """Normalized object size."""
        return self._size

    @property
    def max_scale(self):
        """Maximum scale value."""
        return self._max_scale

    @property
    def display_size(self):
        """Size of display."""
        return (self.WIDTH, self.HEIGHT)

    @property
    def hand1(self):
        """Currently displayed hand1 value."""
        return self._hand1

    @hand1.setter
    def hand1(self, value=0):
        self._show_hands(hand1=value, hand2=self._hand2)

    @property
    def hand2(self):
        """Currently displayed hand2 value."""
        return self._hand2

    @hand2.setter
    def hand2(self, value=0):
        self._show_hands(self._hand1, hand2=value)

    @property
    def alarm1(self):
        """Current alarm1 value."""
        return self._alarm1

    @alarm1.setter
    def alarm1(self, value=None):
        self._alarm1 = value
        self._alarm1_palette[0] = Colors.ORANGE
        if self._alarm1 != None:
            self.alarm1_marker.x, self.alarm1_marker.y = self.dial_to_pixel(
                self._alarm1, center=self._center, radius=self._outside_radius
            )
            self._alarm1_palette.make_opaque(0)
        else:
            self.alarm1_marker.x = self.alarm1_marker.y = 0
            self._alarm1_palette.make_transparent(0)

    @property
    def alarm2(self):
        """Current alarm2 value."""
        if self._num_hands != 2:
            return None
        return self._alarm2

    @alarm2.setter
    def alarm2(self, value=None):
        if self._num_hands != 2:
            return
        self._alarm2 = value
        self._alarm2_palette[0] = Colors.GREEN
        if self._alarm2 != None:
            self.alarm2_marker.x, self.alarm2_marker.y = self.dial_to_pixel(
                self._alarm2, center=self._center, radius=self._outside_radius
            )
            self._alarm2_palette.make_opaque(0)
        else:
            self.alarm2_marker.x = self.alarm2_marker.y = 0
            self._alarm2_palette.make_transparent(0)

    def _show_hands(self, hand1=0, hand2=0):
        """Display hand(s) and move scale plate proportionally. Input
        is normalized for 0.0 (minimum) to 1.0 (maximum), but wraps around for
        any positive or negative floating point value.

        :param float hand1: The first hand position on the scale dial.
        :param float hand1: The second hand position on the scale dial."""

        # Move plate/riser
        if hand1 != self._hand1 or hand2 != self._hand2:
            plate_disp = self._plate_y - (min(2, max(-2, (hand1 + hand2))) * 0.10 / 2)
            _, self.plate.y = self.cart_to_pixel(0.00, plate_disp, size=self._size)
            self.riser.y = self.plate.y

        # Draw hands
        if hand1 != self._hand1:
            self._hand1 = hand1
            hand1_fill = hand1_outline = Colors.ORANGE
            if self._hand1 != min(1.0, max(self._hand1, 0.0)):
                hand1_outline = Colors.RED

            x0, y0 = self.dial_to_pixel(
                self._hand1, center=self._center, radius=self._outside_radius
            )
            x1, y1 = self.dial_to_pixel(
                self._hand1 - 0.25, center=self._center, radius=self._base
            )
            x2, y2 = self.dial_to_pixel(
                self._hand1 + 0.25, center=self._center, radius=self._base
            )
            pointer_1 = Triangle(
                x0,
                y0,
                x1,
                y1,
                x2,
                y2,
                fill=hand1_fill,
                outline=hand1_outline,
            )
            self._hands_group[0] = pointer_1

        if hand2 != self._hand2:
            self._hand2 = hand2
            hand2_fill = hand2_outline = None
            if self._num_hands == 2:
                hand2_fill = hand2_outline = Colors.GREEN
                if self._hand2 != min(1.0, max(self._hand2, 0.0)):
                    hand2_outline = Colors.RED

                x0, y0 = self.dial_to_pixel(
                    self._hand2, center=self._center, radius=self._outside_radius
                )
                x1, y1 = self.dial_to_pixel(
                    self._hand2 - 0.25, center=self._center, radius=self._base
                )
                x2, y2 = self.dial_to_pixel(
                    self._hand2 + 0.25, center=self._center, radius=self._base
                )
                pointer_2 = Triangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=hand2_fill,
                    outline=hand2_outline,
                )
                self._hands_group[1] = pointer_2
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
