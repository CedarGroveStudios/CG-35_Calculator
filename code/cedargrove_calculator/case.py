# SPDX-FileCopyrightText: 2022, 2024 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
cedargrove_calculator.case.py  2024-04-14 v2.2
For the ESP32-S3 4Mb/2Mb Feather and 3.5-inch TFT Capacitive FeatherWing
==============================================

Calculator case graphics classes.

"""

import displayio
import vectorio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label


class Colors:
    BLACK = 0x000000
    BLUE = 0x606060
    GRAY = 0x202020
    GRAY_DK = 0x101010

    black_palette = displayio.Palette(1)
    black_palette[0] = BLACK
    gray_palette = displayio.Palette(1)
    gray_palette[0] = GRAY
    gray_dk_palette = displayio.Palette(1)
    gray_dk_palette[0] = GRAY_DK


# (x, y), (width, height), name, fill_color
# object order: back to front
HP_CASE = [
    ((39, 0), (241, 78), "DISPLAY outline", Colors.gray_dk_palette),
    ((39, 78), (241, 402), "KEYS outline", Colors.gray_palette),
    ((89, 89), (33, 11), "PWR outline", Colors.gray_dk_palette),
    ((106, 89), (17, 11), "PWR switch", Colors.black_palette),
    ((48, 18), (223, 42), "DISPLAY area", Colors.black_palette),
]


class LEDDisplay(displayio.Group):
    def __init__(self, scale=1, display_color=0xFF0000, display=None):
        """Instantiate LED display and build led_display_group."""

        _scale = scale

        FONT_0 = bitmap_font.load_font("/fonts/SevenSeg-12.bdf")

        # Build displayio LED display group
        led_display_group = displayio.Group()

        # LED display label
        self._led_digits = Label(
            font=FONT_0,
            text="",
            color=display_color,
        )
        self._led_digits.anchor_point = (0, 0.5)
        self._led_digits.anchored_position = (57, 40)
        led_display_group.append(self._led_digits)

        super().__init__(scale=_scale)
        self.append(led_display_group)
        return

    @property
    def text(self):
        return self._led_digits.text

    @text.setter
    def text(self, text=""):
        self._led_digits.text = text[0:15]
        return


class CalculatorCase(displayio.Group):
    def __init__(self, display=None):
        """Instantiate case graphic and build case group."""
        self._l_margin = HP_CASE[0][0][0]

        FONT_1 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        # Build displayio case group
        case_group = displayio.Group()

        for part in HP_CASE:
            case_part = vectorio.Rectangle(
                pixel_shader=part[3],
                x=part[0][0],
                y=part[0][1],
                width=part[1][0],
                height=part[1][1],
            )
            case_group.append(case_part)

        # Status message area
        self._status = Label(
            font=FONT_1,
            text="",
            color=None,
        )
        self._status.anchor_point = (0.5, 0.5)
        self._status.anchored_position = (160, 69)
        case_group.append(self._status)

        # Power switch label
        pwr_text = Label(
            font=FONT_1,
            text="OFF" + (" " * 14) + "ON" + (" " * 26) + "CG-35",
            color=Colors.BLACK,
        )
        pwr_text.anchor_point = (0, 0)
        pwr_text.anchored_position = (61, HP_CASE[2][0][1])
        case_group.append(pwr_text)

        super().__init__()
        self.append(case_group)
        return

    @property
    def l_margin(self):
        """Left margin spacing in pixels."""
        return self._l_margin

    @property
    def status(self):
        """Status message text."""
        return self._status

    @status.setter
    def status(self, text=""):
        self._status = text
        return
