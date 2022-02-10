# 10-Segment Bargraph widget
# based on the Lucky Light LED 10-Segment LED Gauge Bar and LML391x controllers
# 2021-12-10 v0.9

import displayio
import vectorio


class Colors:
    # Define a few colors (https://en.wikipedia.org/wiki/Web_colors)
    BLACK = 0x000000
    GRAY = 0x508080
    GRAY_DK = 0x404040
    GREEN_LED = 0x00A000
    RED = 0xFF0000
    YELLOW = 0xFFFF00


class Bargraph(displayio.Group):
    def __init__(
        self,
        units=0,
        center=(0, 0),
        size=1,
        range="VU",
        mode="BAR",
        display_size=(None, None),
    ):
        """Bargraph display widget. Accepts a normalized (0 to 1.0) input
        representing full-scale of a single or stacked bargraph object.

        Emulates the LM391x series of dot/bar display drivers:
        LM3914 Dot/Bar Display Driver (volts; 1.2v full-scale/10 bars)
        LM3915 (dB; 3dB per step, 30dB range/10 bars)
        LM3916 (VU; 10v full-scale; -20, -10, -7, -5, -3, -1, 0, +1, +2, +3dB)
            ( -40, -37, -34, -31, -28, -25, -22, -19, -16, -13, -10, -7, -5, -3, -1, 0, +1, +2, +3dB)

        'VU' range shades the top 4 bars of the single or stacked bargraph YEL,
        RED, RED, RED to represent a typical VU peak range.
        'BAR' mode is a contiguous illumination of segments from the first
        to the segment representing the signal value. 'DOT' mode illuminates
        the signal value segment with a slight glow of the surrounding segments,
        particularly useful when the signal value is zero.

        The current version does not adjust normalized signal input to volts, VU,
        or linear dB scale, nor does it implement DOT mode."""

        self._units = units
        self._origin = center
        self._size = size
        self._range = range
        self._mode = mode
        self._display_size = display_size

        bargraph_group = displayio.Group(scale=self._size)
        chips = displayio.Group()
        self._bars = displayio.Group()

        self._blk_palette = displayio.Palette(1)
        self._blk_palette[0] = Colors.BLACK

        self._red_palette = displayio.Palette(1)
        self._red_palette[0] = Colors.RED
        self._yel_palette = displayio.Palette(1)
        self._yel_palette[0] = Colors.YELLOW
        self._grn_palette = displayio.Palette(1)
        self._grn_palette[0] = Colors.GREEN_LED

        # Draw the DIP packages
        dip_pkg_palette = displayio.Palette(1)
        dip_pkg_palette[0] = Colors.GRAY_DK

        for chip in range(0, self._units):
            upper_left_corner = (self._origin[0] + (100 * chip), self._origin[1])

            dip_pkg = vectorio.Rectangle(
                pixel_shader=dip_pkg_palette,
                x=upper_left_corner[0],
                y=upper_left_corner[1],
                width=100,
                height=40,
            )
            chips.append(dip_pkg)

            _points = [
                (upper_left_corner[0], 40 + upper_left_corner[1]),
                (upper_left_corner[0], 35 + upper_left_corner[1]),
                (4 + upper_left_corner[0], 40 + upper_left_corner[1]),
            ]
            dip_idx = vectorio.Polygon(
                pixel_shader=self._blk_palette,
                points=_points,
            )
            chips.append(dip_idx)

            for i in range(0, 10):
                bar_rect = vectorio.Rectangle(
                    pixel_shader=self._blk_palette,
                    x=upper_left_corner[0] + 2 + (i * 10),
                    y=10 + upper_left_corner[1],
                    width=6,
                    height=20,
                )

                self._bars.append(bar_rect)
        super().__init__()
        self.append(chips)
        self.append(self._bars)

    @property
    def center(self):
        """Bargraph object center."""
        return self._origin

    @property
    def units(self):
        """Number of units."""
        return self._units

    @property
    def size(self):
        """Bargraph object size."""
        return self._size

    @property
    def range(self):
        """Bargraph signal range."""
        return self._range

    @property
    def mode(self):
        """Bargraph display mode."""
        return self._mode

    @property
    def display_size(self):
        """Display size in pixels."""
        return self._display_size

    @property
    def value(self):
        """Currently displayed value."""
        return self._signal

    @value.setter
    def value(self, signal=None):
        self._show_signal(signal)

    # @property
    # def center(self, cluster=0):
    #    """Normalized display coordinates of the object center."""
    #    determine center of cluster specified by the cluster parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    # @center.setter
    # def center(self, cluster=0, x, y):
    #    """Set the normalized display coordinates of the object center."""
    #    procedure for setting all coordinates for a cluster
    #    as specified by the cluster parameter
    #    SHOULD THIS BE A FUNCTION?
    #    return

    def _show_signal(self, signal=None):
        bar = int(round(signal * (self._units * 10), 0))

        for i in range(0, self._units * 10):
            if i <= bar and self._range == "VU":
                if i > ((self._units - 1) * 10) + 6:
                    self._bars[i].pixel_shader = self._red_palette
                elif i == ((self._units - 1) * 10) + 6:
                    self._bars[i].pixel_shader = self._yel_palette
                else:
                    self._bars[i].pixel_shader = self._grn_palette
            else:
                self._bars[i].pixel_shader = self._blk_palette

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
