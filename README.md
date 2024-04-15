# Retro RPN Calculator
The CG-35 is a HP-35-like RPN calculator application for the Adafruit ESP32-S3 Feather and 3.5-inch TFT FeatherWing display with capacitive touch. The calculator
consists of a 10-digit LED display with 20-digit internal calculation precision. The emulator code is augmented by the micropython `udecimal` library adapted for CircuitPython by @jepler (Thank you!).

![The CG-35 Retro RPN Calculator](https://github.com/CedarGroveStudios/CG-35_Calculator/blob/main/photos_graphics/IMG_1988.jpeg)

The CG-35 is a HP-35-like RPN calculator application for the Adafruit ESP32-S3 Feather
and 3.5-inch TFT FeatherWing display with capacitive touch. The calculator
consists of a 10-digit LED display with 20-digit internal calculation
precision.

This application emulates the HP-35 calculator's v2.0 firmware where the change
sign (CHS) key is active only after digit entry has begun. Calculation accuracy
of monadic, dyadic, and trigonometric functions was improved. An error descriptor
message area just below the primary display was added.

The calculator's graphical layout was designed to mimic the aspect ratio of the
original calculator. Because of the relative small size of the buttons,
touchscreen accuracy is important, requiring the use of a capacitive touch
screen rather than a resistive touch screen.

For audible key press and status feedback, connect a piezo speaker from
pin A0 to ground.

* Author(s): JG for Cedar Grove Maker Studios
* GitHub: <https://github.com/CedarGroveStudios/CG-35_Calculator>

Implementation Notes
--------------------
**Hardware:**
* Adafruit 'ESP32-S3 4Mb/2Mb FeatherWing
  <https://www.adafruit.com/product/5477>
* Adafruit 'Adafruit TFT FeatherWing - 3.5" 480x320 Capacitive Touchscreen
  <https://www.adafruit.com/product/5872>

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the ESP32-S3 FeatherWing:
  <https://circuitpython.org/downloads>
* Jeff Epler's adaptation of micropython `udecimal` and `utrig`:
  <https://github.com/jepler/Jepler_CircuitPython_udecimal>
* CedarGrove's `SevenSeg-12.bdf` font:
  <https://github.com/CedarGroveStudios/SevenSeg_font>

Optional/future features:
- Implement display brightness control.
- Adjust for automatic scientific notation conversion for entered values < |1| with a negative exponent > -6. This is an inherent behavior of the Decimal class in micropython, CircuitPython, and CPython.
- Purge the T register when calculating trigonometric functions to fully emulate the HP-35 process.
- Incorporate a selectable degrees/radians mode with indicator (enhancement).
- Incorporate a selectable scientific/engineering/fixed decimal point mode (enhancement).
- Add a setup button for setting initial parameters (enhancement).
