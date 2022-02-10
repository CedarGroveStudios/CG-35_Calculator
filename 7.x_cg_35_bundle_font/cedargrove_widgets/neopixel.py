# NeoPixel widget
# 2021-12-09 v0.8

import displayio
import vectorio
from adafruit_display_shapes.circle import Circle


class Colors:
    # Define a few colors (https://en.wikipedia.org/wiki/Web_colors)
    BLACK = 0x000000
    GRAY = 0x508080
    GRAY_DK = 0x101010


class NeoPixel(displayio.Group):
    def __init__(self, units=0, center=(0, 0), size=1, display_size=(None, None)):
        self._size = size
        self._neopixel_group = displayio.Group(scale=self._size)
        neo_pkg = displayio.Group()
        self._reflector = displayio.Group()

        self._neopixel_units = units
        self._origin = center

        gray_palette = displayio.Palette(1)
        gray_palette[0] = Colors.GRAY
        gray_dk_palette = displayio.Palette(1)
        gray_dk_palette[0] = Colors.GRAY_DK

        for chip in range(0, self._neopixel_units):
            upper_left_corner = (self._origin[0] + (15 * chip), self._origin[1])

            pkg = vectorio.Rectangle(
                pixel_shader=gray_dk_palette,
                x=upper_left_corner[0],
                y=upper_left_corner[1],
                width=15,
                height=15,
            )
            neo_pkg.append(pkg)

            pkg_index = vectorio.Rectangle(
                pixel_shader=gray_palette,
                x=upper_left_corner[0],
                y=14 + upper_left_corner[1],
                width=1,
                height=1,
            )
            neo_pkg.append(pkg_index)

            self._reflect_base = Circle(
                upper_left_corner[0] + 7,
                upper_left_corner[1] + 7,
                6,
                fill=Colors.BLACK,
                outline=None,
            )
            self._reflector.append(self._reflect_base)

        super().__init__()
        self.append(neo_pkg)
        self.append(self._reflector)
        return

    @property
    def center(self):
        """Bargraph object center."""
        return self._origin

    @property
    def units(self):
        """Number of units."""
        return self._neopixel_units

    @property
    def size(self):
        """Bargraph object size."""
        return self._size

    @property
    def display_size(self):
        """Display size in pixels."""
        return self._display_size

    @property
    def neo_group(self):
        return self._reflector


    # @property
    # def center(self, n=0):
    #    """Normalized display coordinates of neopixel object center."""
    #    determine center of neopixel specified by the n parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    # @centersetter
    # def center(self, unit, x, y):
    #    """Set the normalized display coordinates of neopixel object center."""
    #    procedure for setting all coordinates for a pixel's display elements
    #    as specified by the n parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    def show(self, n=None, color=Colors.BLACK):
        """Set the color of the nth neopixel."""
        if n != None:
            self._reflector[n].fill = color
        return

    def fill(self, color=Colors.BLACK):
        """Fill all neopixels with color."""
        for i in range(0, self._neopixel_units):
            self.show(i, color)
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
