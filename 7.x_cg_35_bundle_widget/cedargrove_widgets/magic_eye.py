# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# magic_eye.py
# 2021-12-12 v2.3

import displayio
import vectorio
from math import pi, pow, sin, cos, sqrt
from adafruit_display_shapes.circle import Circle


class Colors:
    # Define a few default colors
    BLACK = 0x000000
    CYAN = 0x00FFFF
    GREEN_DK = 0x005000
    GREEN_LT = 0x00A060


class MagicEye(displayio.Group):
    def __init__(
        self,
        center=(0.50, 0.50),
        size=0.5,
        display_size=(None, None),
        bezel_color=Colors.BLACK,
    ):
        """Instantiate the 6E5 magic eye graphic object for DisplayIO devices.
        Builds a hierarchical DisplayIO group consisting of sub-groups for the
        target, anode, eye, and bezel/cathode.
        Display size in pixels is specified as an integer tuple. If the
        display_size tuple is not specified and an integral display is listed
        in the board class, the display_size tuple will be equal to the
        integral display width and height. The default RGB bezel color is
        0x000000 (black).

        :param float center: The widget center x,y tuple in normalized display
        units. Defaults to (0.5, 0.5).
        :param float size: The widget size factor relative to the display's
        smaller axis. Defaults to 0.5.
        :param integer display_size: The host display's integer width and
        height tuple expressed in pixels. If (None, None) and the host includes
        an integral display, the tuple value is set to (board.DISPLAY.width,
        board.DISPLAY.height).
        :param bezel_color: The integer RGB color value for the outer bezel.
        Recommend setting to display background color. Defaults to 0x000000 (black)."""

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
        self._radius_norm = self._size / 2

        # Target anode and cathode light shield pixel screen values
        self._outside_radius = int(self._radius_norm * min(self.WIDTH, self.HEIGHT))
        self._inside_radius = int(0.90 * self._outside_radius)
        self._shield_radius = int(0.40 * self._outside_radius)

        # Create displayio group layers
        self._anode_group = displayio.Group()  # Target anode and wire shadows
        self._eye_group = displayio.Group()  # Dynamic eye + tarsus shadow wedge
        self._bezel_group = displayio.Group()  # Bezel wedges/doughnut and light shield

        # Define green phosphor target anode
        self._anode_palette = displayio.Palette(1)
        self._anode_palette[0] = Colors.GREEN_LT

        self.target_anode = vectorio.Circle(
            pixel_shader=self._anode_palette,
            radius=self._outside_radius,
            x=self._center[0],
            y=self._center[1],
        )
        self._anode_group.append(self.target_anode)

        # Define wire shadow
        cathode_palette = displayio.Palette(1)
        cathode_palette[0] = Colors.BLACK

        x0, y0 = self.dial_to_pixel(
            0.75, center=self._center, radius=self._inside_radius
        )
        x1, y1 = self.dial_to_pixel(
            0.25, center=self._center, radius=self._inside_radius
        )
        wires = vectorio.Rectangle(
            pixel_shader=cathode_palette,
            x=x0,
            y=y0,
            width=x1 - x0,
            height=1,
        )
        self._anode_group.append(wires)

        # Combined shadow wedge and tarsus polygon points
        self._shadow_palette = displayio.Palette(1)
        self._shadow_palette[0] = Colors.GREEN_DK

        self._overlap_palette = displayio.Palette(1)
        self._overlap_palette[0] = Colors.CYAN

        x1, y1 = self.dial_to_pixel(
            0.35 + (0 * 0.15),
            center=self._center,
            radius=self._outside_radius,
        )
        x2, y2 = self.dial_to_pixel(
            0.65 - (0 * 0.15),
            center=self._center,
            radius=self._outside_radius,
        )
        _points = [
            self._center,
            (x1, y1),
            (x1, self._center[1] + self._outside_radius),
            (x2, self._center[1] + self._outside_radius),
            (x2, y2),
        ]
        self.eye = vectorio.Polygon(
            pixel_shader=self._shadow_palette,
            points=_points,
        )
        self._eye_group.append(self.eye)

        # Define bezel
        self._bezel_palette = displayio.Palette(1)
        if bezel_color == None:
            self._bezel_color = Colors.BLACK
        else:
            self._bezel_color = bezel_color
        self._bezel_palette[0] = self._bezel_color

        bezel_resolution = self._outside_radius * 2
        bezel_range_min = int(round(0.25 * bezel_resolution, 0))
        bezel_range_max = int(round(0.75 * bezel_resolution, 0))
        bezel_min = self.dial_to_pixel(
            0.25, center=self._center, radius=self._outside_radius
        )
        bezel_max = self.dial_to_pixel(
            0.75, center=self._center, radius=self._outside_radius
        )

        _points = []
        for i in range(bezel_range_min, bezel_range_max + 1):
            _points.append(
                self.dial_to_pixel(
                    i / bezel_resolution,
                    center=self._center,
                    radius=self._outside_radius,
                )
            )
        _points.append((bezel_max[0], self._center[1] + self._outside_radius + 2))
        _points.append((bezel_min[0], self._center[1] + self._outside_radius + 2))
        doughnut_mask = vectorio.Polygon(
            pixel_shader=self._bezel_palette,
            points=_points,
        )
        self._bezel_group.append(doughnut_mask)

        bezel_mask = Circle(
            self._center[0],
            self._center[1],
            self._outside_radius,
            fill=None,
            outline=self._bezel_color,
            stroke=2,
        )
        self._bezel_group.append(bezel_mask)

        # Define cathode light shield
        self._cathode_shield_group = displayio.Group()
        cathode_shield = vectorio.Circle(
            pixel_shader=cathode_palette,
            radius=self._shield_radius,
            x=self._center[0],
            y=self._center[1],
        )
        self._bezel_group.append(cathode_shield)

        # Arrange image group layers
        super().__init__()
        self.append(self._anode_group)
        self.append(self._eye_group)
        self.append(self._bezel_group)

        self._eye_value = 1
        self._show_signal(0)  # Plot no signal shadow wedge
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
    def display_size(self):
        """Size of display."""
        return (self.WIDTH, self.HEIGHT)

    @property
    def value(self):
        """Currently displayed value."""
        return self._eye_value

    @value.setter
    def value(self, signal=0):
        signal = min(max(0, signal), 2.0)
        self._show_signal(signal)

    def _show_signal(self, signal=0):
        """Plot the MagicEye shadow wedge. Input is a positive floating point
        value normalized for 0.0 to 1.0 (no signal to full signal) within the
        100-degree shadow wedge, but accepts a signal value up to and including
        2.0 (signal overlap).

        :param eye_normal: The normalized floating point signal  value for the
        shadow wedge. Defaults to 0 (no signal)."""

        if signal != self._eye_value:
            self._eye_value = signal
            # Combined shadow wedge and tarsus polygon points
            x1, y1 = self.dial_to_pixel(
                0.35 + (self._eye_value * 0.15),
                center=self._center,
                radius=self._outside_radius,
            )
            x2, y2 = self.dial_to_pixel(
                0.65 - (self._eye_value * 0.15),
                center=self._center,
                radius=self._outside_radius,
            )
            _points = [
                self._center,
                (x1, y1),
                (x1, self._center[1] + self._outside_radius),
                (x2, self._center[1] + self._outside_radius),
                (x2, y2),
            ]

            if self._eye_value > 1.0:
                self.eye.pixel_shader = self._overlap_palette
            else:
                self.eye.pixel_shader = self._shadow_palette

            self.eye.points = _points
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
