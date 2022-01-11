# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# cedargrove_calculator.case.py
# 2022-01-02 v1.2

import board
import displayio
import vectorio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label


class Colors:
    BLACK = 0x000000
    GRAY = 0x101010
    GRAY_DK = 0x080808

    black_palette = displayio.Palette(1)
    black_palette[0] = BLACK
    gray_palette = displayio.Palette(1)
    gray_palette[0] = GRAY
    gray_dk_palette = displayio.Palette(1)
    gray_dk_palette[0] = GRAY_DK


# (x, y), (width, height), name, fill_color
# object order: back to front
HP_CASE = [
    ((0.00, 0.00), (2.16, 0.70), "DISPLAY outline", Colors.gray_dk_palette),
    ((0.00, 0.70), (2.16, 3.60), "KEYS outline", Colors.gray_palette),
    ((0.45, 0.80), (0.30, 0.10), "PWR outline", Colors.gray_dk_palette),
    ((0.60, 0.80), (0.15, 0.10), "PWR switch", Colors.black_palette),
]


class CalculatorCase(displayio.Group):
    def __init__(self, debug=False):
        """Instantiate the CalculatorCase graphic.
        Builds the displayio button_group."""

        WIDTH = board.DISPLAY.width
        HEIGHT = board.DISPLAY.height

        self._l_margin = (WIDTH // 2) - int(round(HP_CASE[0][1][0] / 4.3 * HEIGHT / 2, 0))

        # FONT_0 = bitmap_font.load_font("/fonts/brutalist-6.bdf")
        FONT_0 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        # Build displayio case group
        case_group = displayio.Group()

        for i in HP_CASE:
            case_element = vectorio.Rectangle(
                pixel_shader=i[3],
                x=int(round(i[0][0] / 4.3 * HEIGHT, 0)) + self._l_margin,
                y=int(round(i[0][1] / 4.3 * HEIGHT, 0)),
                width=int(round(i[1][0] / 4.3 * HEIGHT, 0)),
                height=int(round(i[1][1] / 4.3 * HEIGHT, 0)),
            )
            case_group.append(case_element)

        # Power switch
        pwr_text = Label(
            font=FONT_0, text="OFF" + (" " * 14) + "ON" + (" " * 26) + "CG-35", color=Colors.BLACK
        )
        pwr_text.anchor_point = (0, 0)
        pwr_text.anchored_position = (
            int(round(0.2 / 4.3 * HEIGHT, 0)) + self._l_margin,
            int(round(HP_CASE[3][0][1] / 4.3 * HEIGHT, 0)),
        )
        case_group.append(pwr_text)

        super().__init__()
        self.append(case_group)
        return

    @property
    def l_margin(self):
        """Left margin spacing in pixels."""
        return self._l_margin
