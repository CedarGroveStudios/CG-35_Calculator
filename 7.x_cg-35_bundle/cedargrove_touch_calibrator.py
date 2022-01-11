# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# cedargrove_touch_calibrator.py
# 2021-12-30 v1.2

import board
import time
import displayio
import vectorio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
import adafruit_touchscreen
from simpleio import map_range


class Colors:
    BLUE_DK = 0x000060
    RED = 0xFF0000
    WHITE = 0xFFFFFF


def touch_calibrator(rotation=None, repl_only=False):
    """On-screen touchscreen calibrator function for built-in displays. To use,
    include the following two lines in the calling module or type into the REPL:

    from cedargrove_touch_calibrator import touch_calibrator
    touch_calibrator()

    To override the display's previous rotation value, specify a rotation value
    (in degrees: 0, 90, 180, 270) when calling the calibrator function:

    touch_calibrator(rotation=90)

    When the test screen appears, use a stylus to swipe to the four sides
    of the visible display area. As the screen is calibrated, the small red
    square tracks the stylus tip (repl_only=False). Minimum and maximum
    calibration values will display on the screen and in the REPL. The REPL
    values can be copied and pasted into the calling code's touchscreen
    instantiation statement.

    :param int rotation: Display rotation value in degrees. Only values of
    None, 0, 90, 180, and 270 degrees are accepted. Defaults to None, the
    previous orientation of the display.
    :param bool repl_only: If False, calibration values are shown on the screen
    and printed to the REPL. If True, the values are only printed to the REPL.
    Default value is False.
    """

    display = board.DISPLAY
    if rotation:  # Override display rotation
        display.rotation = rotation
    else:
        rotation = display.rotation
    WIDTH = board.DISPLAY.width
    HEIGHT = board.DISPLAY.height

    if not repl_only:
        display_group = displayio.Group()
        display.show(display_group)

    # Instantiate touch screen without calibration or display size parameters
    if rotation == 0:
        ts = adafruit_touchscreen.Touchscreen(
            board.TOUCH_XL,
            board.TOUCH_XR,
            board.TOUCH_YD,
            board.TOUCH_YU,
            # calibration=((5200, 59000), (5250, 59500)),
            # size=(WIDTH, HEIGHT),
        )

    elif rotation == 90:
        ts = adafruit_touchscreen.Touchscreen(
            board.TOUCH_YU,
            board.TOUCH_YD,
            board.TOUCH_XL,
            board.TOUCH_XR,
            # calibration=((5250, 59500), (5200, 59000)),
            # size=(WIDTH, HEIGHT),
        )

    elif rotation == 180:
        ts = adafruit_touchscreen.Touchscreen(
            board.TOUCH_XR,
            board.TOUCH_XL,
            board.TOUCH_YU,
            board.TOUCH_YD,
            # calibration=((5200, 59000), (5250, 59500)),
            # size=(WIDTH, HEIGHT),
        )

    elif rotation == 270:
        ts = adafruit_touchscreen.Touchscreen(
            board.TOUCH_YD,
            board.TOUCH_YU,
            board.TOUCH_XR,
            board.TOUCH_XL,
            # calibration=((5250, 59500), (5200, 59000)),
            # size=(WIDTH, HEIGHT),
        )
    else:
        raise ValueError("Rotation value must be 0, 90, 180, or 270")

    if not repl_only:
        FONT_0 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

        coordinates = Label(
            font=FONT_0,
            text="calib: ((x_min, x_max), (y_min, y_max))",
            color=Colors.WHITE,
        )
        coordinates.anchor_point = (0.5, 0.5)
        coordinates.anchored_position = (WIDTH // 2, HEIGHT // 4)

        display_rotation = Label(
            font=FONT_0,
            text="rotation: " + str(rotation),
            color=Colors.WHITE,
        )
        display_rotation.anchor_point = (0.5, 0.5)
        display_rotation.anchored_position = (WIDTH // 2, HEIGHT // 4 - 30)

        target_palette = displayio.Palette(1)
        target_palette[0] = Colors.BLUE_DK
        boundary1 = vectorio.Rectangle(
            pixel_shader=target_palette,
            x=2,
            y=2,
            width=WIDTH - 4,
            height=HEIGHT - 4,
        )

        target_palette = displayio.Palette(1)
        target_palette[0] = Colors.RED
        boundary2 = vectorio.Rectangle(
            pixel_shader=target_palette,
            x=0,
            y=0,
            width=WIDTH,
            height=HEIGHT,
        )

        pen = vectorio.Rectangle(
            pixel_shader=target_palette,
            x=WIDTH // 2,
            y=HEIGHT // 2,
            width=10,
            height=10,
        )

        display_group.append(boundary2)
        display_group.append(boundary1)
        display_group.append(pen)
        display_group.append(coordinates)
        display_group.append(display_rotation)

    # Reset x and y values to scale center
    x_min = x_max = y_min = y_max = 65535 // 2

    print("Touchscreen Calibrator")
    print("  Use a stylus to swipe to the four sides")
    print("  of the visible display area.")
    print(" ")
    print(f"  rotation: {rotation}")
    print("  Calibration values follow:")
    print(" ")

    while True:
        time.sleep(0.100)
        touch = ts.touch_point
        if touch:
            if not repl_only:
                pen.x = int(map_range(touch[0], x_min, x_max, 0, WIDTH)) - 5
                pen.y = int(map_range(touch[1], y_min, y_max, 0, HEIGHT)) - 5

            x_min = min(x_min, touch[0])
            x_max = max(x_max, touch[0])
            y_min = min(y_min, touch[1])
            y_max = max(y_max, touch[1])

            print(f"(({x_min}, {x_max}), ({y_min}, {y_max}))")
            if not repl_only:
                coordinates.text = f"calib: (({x_min}, {x_max}), ({y_min}, {y_max}))"
    return
