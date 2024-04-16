# SPDX-FileCopyrightText: 2022, 2024 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
cedargrove_calculator.buttons.py  2024-03-11 v2.0
modified for 3.5-inch TFT Capacitive FeatherWing with Feather RP2040
=================================================

Calculator buttons class.

* Author(s): JG for Cedar Grove Maker Studios
"""

import board
import time
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from simpleio import tone


class Colors:
    BLACK = 0x000000
    BLUE = 0x4040F0
    GRAY = 0x202020
    GRAY_DK = 0x101010
    RED = 0xFF0000
    WHITE = 0xC0C0C0
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
    (( 61, 123), (29, 22), "x^y", Colors.BLACK, Colors.OUTLINE),
    ((103, 123), (29, 22), "LOG", Colors.BLACK, Colors.OUTLINE),
    ((146, 123), (29, 22), "LN", Colors.BLACK, Colors.OUTLINE),
    ((187, 123), (29, 22), "e^x", Colors.BLACK, Colors.OUTLINE),
    ((230, 123), (29, 22), "CLR", Colors.BLUE, Colors.OUTLINE),
    (( 61, 167), (29, 22), "√x", Colors.BLACK, Colors.OUTLINE),
    ((103, 167), (29, 22), "ARC", Colors.BLACK, Colors.OUTLINE),
    ((146, 167), (29, 22), "SIN", Colors.BLACK, Colors.OUTLINE),
    ((187, 167), (29, 22), "COS", Colors.BLACK, Colors.OUTLINE),
    ((230, 167), (29, 22), "TAN", Colors.BLACK, Colors.OUTLINE),
    (( 61, 212), (29, 22), "1/x", Colors.BLACK, Colors.OUTLINE),
    ((103, 212), (29, 22), "x<>y", Colors.BLACK, Colors.OUTLINE),
    ((146, 212), (29, 22), "R", Colors.BLACK, Colors.OUTLINE),
    ((187, 212), (29, 22), "STO", Colors.BLACK, Colors.OUTLINE),
    ((230, 212), (29, 22), "RCL", Colors.BLACK, Colors.OUTLINE),
    (( 61, 257), (69, 22), "ENTER", Colors.BLUE, Colors.OUTLINE),
    ((146, 257), (29, 22), "CHS", Colors.BLUE, Colors.OUTLINE),
    ((187, 257), (29, 22), "EEX", Colors.BLUE, Colors.OUTLINE),
    ((230, 257), (29, 22), "CLX", Colors.BLUE, Colors.OUTLINE),
    (( 61, 301), (29, 22), "-", Colors.BLUE, Colors.OUTLINE),
    ((105, 301), (33, 22), "7", Colors.WHITE, Colors.OUTLINE),
    ((165, 301), (33, 22), "8", Colors.WHITE, Colors.OUTLINE),
    ((225, 301), (33, 22), "9", Colors.WHITE, Colors.OUTLINE),
    (( 61, 346), (22, 22), "+", Colors.BLUE, Colors.OUTLINE),
    ((105, 346), (33, 22), "4", Colors.WHITE, Colors.OUTLINE),
    ((165, 346), (33, 22), "5", Colors.WHITE, Colors.OUTLINE),
    ((225, 346), (33, 22), "6", Colors.WHITE, Colors.OUTLINE),
    (( 61, 391), (22, 22), "*", Colors.BLUE, Colors.OUTLINE),
    ((105, 391), (33, 22), "1", Colors.WHITE, Colors.OUTLINE),
    ((165, 391), (33, 22), "2", Colors.WHITE, Colors.OUTLINE),
    ((225, 391), (33, 22), "3", Colors.WHITE, Colors.OUTLINE),
    (( 61, 435), (22, 22), "÷", Colors.BLUE, Colors.OUTLINE),
    ((105, 435), (33, 22), "0", Colors.WHITE, Colors.OUTLINE),
    ((165, 435), (33, 22), ".", Colors.WHITE, Colors.OUTLINE),
    ((225, 435), (33, 22), "π", Colors.WHITE, Colors.OUTLINE),
]


class CalculatorButtons(displayio.Group):
    def __init__(self, l_margin=0, timeout=1.0, click=True,  display=None, touch=None):
        """Instantiate on-screen buttons and build button_group."""

        self._timeout = timeout
        self._click = click
        self._l_margin = l_margin
        self.ts = touch
        WIDTH = display.width
        HEIGHT = display.height
        SIZE_FACTOR = 1.2

        # Create a list of button names for button creation
        self._button_names = [name[2] for name in HP_BUTTONS]

        self.FONT_0 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        # Build displayio button group
        self._buttons = []
        self._buttons_index = []  # The list of buttons used for detection
        button_group = displayio.Group()

        # Create the displayio button definitions
        for key in HP_BUTTONS:
            button = Button(
                x=key[0][0],
                y=key[0][1],
                width=int(key[1][0] * SIZE_FACTOR),
                height=int(key[1][1] * SIZE_FACTOR),
                style=Button.RECT,
                fill_color=key[3],
                outline_color=key[4],
                name=key[2],
                label=key[2],
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
        touch = self.ts.points
        if touch:
            for button in self._buttons:
                if button.contains(touch[0]):  # read only the first point touched
                    button.selected = True
                    if self._click:
                        # Make a click sound when button is pressed
                        tone(board.A0, 2000, 0.025, length=8)
                    button_pressed = button.name
                    button_name = self._buttons_index.index(button_pressed)
                    timeout_beep = False
                    while self.ts.points:
                        time.sleep(0.1)
                        hold_time += 0.1
                        if hold_time >= self._timeout and not timeout_beep:
                            if self._click:
                                # Play a beep tone if button is held
                                tone(board.A0, 1320, 0.100, length=8)
                            timeout_beep = True
                    button.selected = False
                    if self._click:
                        # Make a click sound when button is released
                        tone(board.A0, 2000, 0.025, length=8)
        return button_pressed, button_name, hold_time
