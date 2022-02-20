# SPDX-FileCopyrightText: 2022 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
cedargrove_calculator.buttons.py  2022-02-19 v1.0
=================================================

Calculator buttons class.

* Author(s): JG for Cedar Grove Maker Studios
"""

import board
import time
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
import adafruit_touchscreen
from simpleio import tone


class Colors:
    BLACK = 0x000000
    BLUE = 0x2020D0
    GRAY = 0x101010
    GRAY_DK = 0x080808
    RED = 0xFF0000
    WHITE = 0xA0A0A0
    OUTLINE = GRAY_DK

    black_palette = displayio.Palette(1)
    black_palette[0] = BLACK
    gray_palette = displayio.Palette(1)
    gray_palette[0] = GRAY
    gray_dk_palette = displayio.Palette(1)
    gray_dk_palette[0] = GRAY_DK


# (x, y), (width, height), name, fill_color, outline_color, pressed_color
# object order: back to front
HP_BUTTONS = [
    ((0.20, 1.1), (0.26, 0.20), "x^y", Colors.BLACK, Colors.OUTLINE),
    ((0.57, 1.1), (0.26, 0.20), "LOG", Colors.BLACK, Colors.OUTLINE),
    ((0.96, 1.1), (0.26, 0.20), "LN", Colors.BLACK, Colors.OUTLINE),
    ((1.33, 1.1), (0.26, 0.20), "e^x", Colors.BLACK, Colors.OUTLINE),
    ((1.71, 1.1), (0.26, 0.20), "CLR", Colors.BLUE, Colors.OUTLINE),
    ((0.20, 1.5), (0.26, 0.20), "√x", Colors.BLACK, Colors.OUTLINE),
    ((0.57, 1.5), (0.26, 0.20), "ARC", Colors.BLACK, Colors.OUTLINE),
    ((0.96, 1.5), (0.26, 0.20), "SIN", Colors.BLACK, Colors.OUTLINE),
    ((1.33, 1.5), (0.26, 0.20), "COS", Colors.BLACK, Colors.OUTLINE),
    ((1.71, 1.5), (0.26, 0.20), "TAN", Colors.BLACK, Colors.OUTLINE),
    ((0.20, 1.9), (0.26, 0.20), "1/x", Colors.BLACK, Colors.OUTLINE),
    ((0.57, 1.9), (0.26, 0.20), "x<>y", Colors.BLACK, Colors.OUTLINE),
    ((0.96, 1.9), (0.26, 0.20), "R", Colors.BLACK, Colors.OUTLINE),
    ((1.33, 1.9), (0.26, 0.20), "STO", Colors.BLACK, Colors.OUTLINE),
    ((1.71, 1.9), (0.26, 0.20), "RCL", Colors.BLACK, Colors.OUTLINE),
    ((0.20, 2.3), (0.62, 0.20), "ENTER", Colors.BLUE, Colors.OUTLINE),
    ((0.96, 2.3), (0.26, 0.20), "CHS", Colors.BLUE, Colors.OUTLINE),
    ((1.33, 2.3), (0.26, 0.20), "EEX", Colors.BLUE, Colors.OUTLINE),
    ((1.71, 2.3), (0.26, 0.20), "CLX", Colors.BLUE, Colors.OUTLINE),
    ((0.20, 2.7), (0.20, 0.20), "-", Colors.BLUE, Colors.OUTLINE),
    ((0.59, 2.7), (0.30, 0.20), "7", Colors.WHITE, Colors.OUTLINE),
    ((1.13, 2.7), (0.30, 0.20), "8", Colors.WHITE, Colors.OUTLINE),
    ((1.67, 2.7), (0.30, 0.20), "9", Colors.WHITE, Colors.OUTLINE),
    ((0.20, 3.1), (0.20, 0.20), "+", Colors.BLUE, Colors.OUTLINE),
    ((0.59, 3.1), (0.30, 0.20), "4", Colors.WHITE, Colors.OUTLINE),
    ((1.13, 3.1), (0.30, 0.20), "5", Colors.WHITE, Colors.OUTLINE),
    ((1.67, 3.1), (0.30, 0.20), "6", Colors.WHITE, Colors.OUTLINE),
    ((0.20, 3.5), (0.20, 0.20), "*", Colors.BLUE, Colors.OUTLINE),
    ((0.59, 3.5), (0.30, 0.20), "1", Colors.WHITE, Colors.OUTLINE),
    ((1.13, 3.5), (0.30, 0.20), "2", Colors.WHITE, Colors.OUTLINE),
    ((1.67, 3.5), (0.30, 0.20), "3", Colors.WHITE, Colors.OUTLINE),
    ((0.20, 3.9), (0.20, 0.20), "÷", Colors.BLUE, Colors.OUTLINE),
    ((0.59, 3.9), (0.30, 0.20), "0", Colors.WHITE, Colors.OUTLINE),
    ((1.13, 3.9), (0.30, 0.20), ".", Colors.WHITE, Colors.OUTLINE),
    ((1.67, 3.9), (0.30, 0.20), "π", Colors.WHITE, Colors.OUTLINE),
]


class CalculatorButtons(displayio.Group):
    def __init__(self, l_margin=0, timeout=1.0, click=True):
        """Instantiate the Calculator on-screen touch buttons the PyPortal
        Titano. Builds the displayio button_group. Assumes that the display
        rotation is 90 degrees (portrait orientation)."""

        self._timeout = timeout
        self._click = click
        self._l_margin = l_margin
        WIDTH = board.DISPLAY.width
        HEIGHT = board.DISPLAY.height

        # Create a simple indexed list of button names for button creation
        self._button_names = []
        for i in range(0, len(HP_BUTTONS)):
            self._button_names.append(HP_BUTTONS[2])

        # Instantiate touch screen
        self.ts = adafruit_touchscreen.Touchscreen(
            board.TOUCH_YU,
            board.TOUCH_YD,
            board.TOUCH_XL,
            board.TOUCH_XR,
            calibration=((8807, 56615), (4984, 58063)),  # Titano calibration
            size=(WIDTH, HEIGHT),
            samples=4,  # Default: 4 samples
            z_threshold=8000,  # Default: 10000
        )

        self.FONT_0 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        # Build displayio button group
        self._buttons = []
        self._buttons_index = []  # The list of buttons used for detection
        button_group = displayio.Group()

        # Create the displayio button definitions
        for i in HP_BUTTONS:
            button = Button(
                x=int(round(i[0][0] / 4.3 * HEIGHT, 0)) + self._l_margin,
                y=int(round(i[0][1] / 4.3 * HEIGHT, 0)),
                width=int(round(i[1][0] / 4.3 * HEIGHT, 0)),
                height=int(round(i[1][1] / 4.3 * HEIGHT, 0)),
                style=Button.RECT,
                fill_color=i[3],
                outline_color=i[4],
                name=i[2],
                label=i[2],
                label_font=self.FONT_0,
                label_color=Colors.WHITE,
                selected_fill=Colors.RED,
                selected_outline=Colors.RED,
            )
            if button.fill_color == Colors.WHITE:
                button.label_color = Colors.BLACK
            button_group.append(button)
            self._buttons.append(button)
            self._buttons_index.append(button.name)

        super().__init__()
        self.append(button_group)
        return

    @property
    def timeout(self):
        """Button timeout duration setting."""
        return self._timeout

    @timeout.setter
    def timeout(self, hold_time=1.0):
        """Select timeout duration value in seconds, positive float value."""
        if hold_time < 0 or hold_time >= 10:
            print(
                "Invalid button timeout duration value. Must be between 0 and 10 seconds."
            )
            return
        self._timeout = hold_time
        return

    def read_buttons(self):
        button_pressed = button_name = None
        hold_time = 0
        touch = self.ts.touch_point
        if touch:
            for button in self._buttons:
                if button.contains(touch):
                    button.selected = True
                    if self._click:
                        # Make a click sound when button is pressed
                        tone(board.A0, 3000, 0.001, length=8)
                    button_pressed = button.name
                    button_name = self._buttons_index.index(button_pressed)
                    timeout_beep = False
                    while self.ts.touch_point:
                        time.sleep(0.1)
                        hold_time += 0.1
                        if hold_time >= self._timeout and not timeout_beep:
                            if self._click:
                                # Play a beep tone if button is held
                                tone(board.A0, 1320, 0.050, length=8)
                            timeout_beep = True
                    button.selected = False
                    if self._click:
                        # Make a click sound when button is released
                        tone(board.A0, 3000, 0.001, length=8)
        return button_pressed, button_name, hold_time
