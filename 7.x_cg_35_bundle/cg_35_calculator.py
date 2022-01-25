# SPDX-FileCopyrightText: 2022 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
cg_35_calculator.py  2022-01-24 v0.824 ALPHA
============================================

An HP-35-like RPN calculator application for the Adafruit PyPortal Titano. The
calculator sports a 10-digit LED display with 20-digit internal calculation
precision.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------
**Hardware:**
* Adafruit 'PyPortal Titano
  <https://www.adafruit.com/product/4444>

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  <https://circuitpython.org/downloads>
* Jeff Epler's adaptation of micropython udecimal and utrig:
  <https://github.com/jepler/Jepler_CircuitPython_udecimal>

to do before v1.0 beta release:
    - add exponent digit entry
    - convert trigometric functions to degrees
optional/future features:
    - degrees/radians switch
    - scientific/engineering/fixed decimal point mode
"""

import board
import displayio
import time
import gc

gc.collect()  # Clean-up memory heap space

from cedargrove_calculator.buttons_pyportal import CalculatorButtons
from cedargrove_calculator.case import CalculatorCase
from cedargrove_widgets.bubble_display import BubbleDisplay

# from cedargrove_sdcard import SDCard
from jepler_udecimal import Decimal, getcontext, setcontext, localcontext, ROUND_HALF_UP
import jepler_udecimal.utrig  # Needed for trig functions in Decimal

VISIBLE_CASE = True

t0 = time.monotonic()  # Reset start-up time counter
gc.collect()  # Clean-up memory heap space

# Create the primary displayio.Group layer
calculator = displayio.Group()

# Rotate the display to portrait orientation
display = board.DISPLAY
display.rotation = 90
display.brightness = 1.0  # Titano: 0.55 max for camera image

# Instatiate case group and buttons class
case_group = CalculatorCase(visible=VISIBLE_CASE)
buttons = CalculatorButtons(
    l_margin=case_group.l_margin, timeout=10, click=True
)

# Instantiate the BubbleDisplay widget: 15-digit display, dedicated decimal point
led_display = BubbleDisplay(
    units=5, digits=3, mode="HP-35", center=(0.5, 0.08), size=0.58
)

gc.collect()  # Clean-up memory heap space

# Initiate the display, memory, and stack
DISPLAY_C = " 0."
DISPLAY_E = " 00"
X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")

# Sets the default internal precision and exponent range
getcontext().prec = 20
getcontext().Emax = 99
getcontext().Emin = -99
#getcontext().rounding = ROUND_HALF_UP

# Add the case, bubble display, and button displayio layers
calculator.append(case_group)
calculator.append(led_display)
calculator.append(buttons)


def clr(register=None):
    """Clear all or just X_REG; None for all registers. Clears the display."""
    global DISPLAY_C, DISPLAY_E, X_REG, Y_REG, Z_REG, T_REG, MEM
    if not register:
        # Clear stack registers, memory, and display
        DISPLAY_C = " 0."
        DISPLAY_E = " 00"
        X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")
    elif register == "x":
        # Clear X_REG and display
        DISPLAY_C = " 0."
        DISPLAY_E = " 00"
        X_REG = Decimal("0")
    else:
        return False  # No register specified
    return True


def get_key():
    """Get pressed key name. This is a blocking method (for now)."""
    key_name = None
    while not key_name:
        key_name, _, hold_time = buttons.read_buttons()
    # print(f"get_key: name:{key_name:5s} hold_time:{hold_time:5.3f}s")
    return key_name


def push_stack():
    """Push stack values; T_REG is lost."""
    global X_REG, Y_REG, Z_REG, T_REG
    T_REG = Z_REG
    Z_REG = Y_REG
    Y_REG = X_REG
    return


def pull_stack():
    """Pull (drop) stack values; place "0" into T_REG."""
    global X_REG, Y_REG, Z_REG, T_REG
    X_REG = Y_REG
    Y_REG = Z_REG
    Z_REG = T_REG
    T_REG = Decimal("0")
    return


def roll_stack():
    """Roll stack values; place X_REG into T_REG."""
    global X_REG, Y_REG, Z_REG, T_REG
    temp = X_REG
    X_REG = Y_REG
    Y_REG = Z_REG
    Z_REG = T_REG
    T_REG = temp
    return


def convert_display_to_decimal(coefficient=" 0.", exponent="   "):
    """Convert display text to an equivalent Decimal value."""
    sign = coefficient[0]
    coefficient = coefficient[1:12]
    exponent = exponent[0:3]

    # Reformat sign for decimal value conversion
    if sign == " ":
        sign = "+"

    # Clean up and reformat coefficient
    while coefficient.find(" ") >= 0:
        coefficient = coefficient.split(" ", 1)[0] + coefficient.split(" ", 1)[1]
    if coefficient[0] == ".":
        coefficient = "0" + coefficient

    # Clean up and reformat exponent
    while exponent.find(" ") >= 0:
        exponent = exponent.split(" ", 1)[0] + exponent.split(" ", 1)[1]
    if exponent == "":
        exponent = "0"
    exponent = "E" + str(int(exponent))
    return Decimal(sign + coefficient + exponent)


def convert_decimal_to_display(value=Decimal("0")):
    """Convert a Decimal value into the equivalent display text."""
    # Round to 10-digit precision and convert to string
    if value.is_finite():
        print("-" * 20)
        print("original value", value)
        getcontext().precision = 10
        print("start",value)
        #value = value.quantize(Decimal("1000000000E-00"))
        #getcontext().prec = 10
        #print("quantize", value)
        value = value * Decimal("1.")
        print("after multiply", value)
        getcontext().prec = 20
        #print(value)
    else:
        value = Decimal("0")
    decimal_text = str(value)
    print("decimal_text", decimal_text)

    # Separate coefficient from exponent
    if decimal_text.find("E") >=0:
        coefficient, exponent = decimal_text.split("E", 1)
    else:
        coefficient = decimal_text
        exponent = " 00"

    print("* coefficient, exponent", coefficient, exponent)

    # Retain "-" as sign; add " " if no neg sign (positive value)
    if coefficient[0] != "-":
        coefficient = " " + coefficient
    print("coefficient", coefficient, len(coefficient))

    # If no decimal point in coefficient, add one to the end
    if coefficient.find(".") < 0 and len(coefficient) < 12:
        coefficient = coefficient + "."

    # Remove leading zeros except at start of digit entry
    if coefficient[1:] != "0.":
        while coefficient.find(".") > 1 and coefficient[1] == "0":
            coefficient = coefficient[0] + coefficient[2:]

    # Remove trailing zeros from coefficient  ERROR?
    while coefficient.find(".") <= 12 and coefficient[-1] == "0":
        coefficient = coefficient[0:-1]

    # Don't display a minus zero coefficient
    if coefficient == "-0.":
        coefficient = " 0."

    print("** coefficient, exponent", coefficient, exponent)

    # If no exponent separator or coefficient is zero, blank the exponent value
    if decimal_text.find("E") < 0 or coefficient[1:] == "0.":
        exponent = "   "
    else:
        exponent = decimal_text.split("E", 1)[1]

    print("*** coefficient, exponent", coefficient, exponent)

    return coefficient, exponent


def print_stack():
    """Print stack registers and auxillary memory."""
    print("-" * 32)
    print(
        f"D.X_REG:  {X_REG}  DISPLAY: '{convert_decimal_to_display(X_REG)[0] + convert_decimal_to_display(X_REG)[1]}'"
    )
    print(f"D.Y_REG:  {Y_REG}")
    print(f"D.Z_REG:  {Z_REG}")
    print(f"D.T_REG:  {T_REG}")
    print(f"D.MEM  :  {MEM}")
    print("-" * 32)
    return


def show_display_reg():
    """Display contents of DISPLAY registers."""
    global DISPLAY_C, DISPLAY_E
    coefficient = DISPLAY_C
    exponent = DISPLAY_E
    if exponent[1:3] == "00":
        exponent = "   "
    # If needed, pad coefficient with spaces
    coefficient = coefficient + (" " * (12 - len(coefficient)))
    led_display.text = coefficient + exponent
    return


def display_error():
    """Show error indicator on display."""
    global error_flag
    clr()
    led_display.text = "---------------"
    error_flag = True
    return


def update_x_reg():
    """Move DISPLAY registers' content to the X_REG."""
    global X_REG, DISPLAY_C, DISPLAY_E
    if DISPLAY_E == "-00":
        DISPLAY_E = " 00"
    X_REG = convert_display_to_decimal(DISPLAY_C, DISPLAY_E)
    return


def display_x_reg():
    # Update the LED display with X_REG value
    global X_REG
    coefficient, exponent = convert_decimal_to_display(X_REG)
    DISPLAY_C = coefficient
    DISPLAY_E = exponent
    # If needed, pad coefficient with spaces
    coefficient = coefficient + (" " * (12 - len(coefficient)))
    led_display.text = coefficient + exponent
    return

display.show(calculator)

gc.collect()
free_memory = gc.mem_free()
frame = time.monotonic() - t0
print("CG-35 Calculator    Cedar Grove Studios")
print(f"setup: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb")
led_display.text = f"{frame:5.02f}    {free_memory/1000:6.03f}"
time.sleep(1)

arc_flag = False
eex_flag = False
dp_flag = False
digit_entry = False
automatic_entry = False

clr()
display_x_reg()

while True:
    t0 = time.monotonic()

    key_name = get_key()

    # Display Entry Keys Cluster
    if key_name in (
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        ".",
        "CHS",
        "EEX",
    ):
        # print("display entry key", "digit entry mode:", digit_entry)
        error_flag = False
        if not digit_entry:
            # Prepare for digit entry when previous operation has finished
            if automatic_entry:
                push_stack()  #  Automatic ENTER -- only after calculation
                automatic_entry = False
            clr("x")
            eex_flag = dp_flag = False
            digit_entry = True

        if (not eex_flag) and digit_entry and len(DISPLAY_C) < 12 and (key_name not in ("CHS", "EEX")):
            if DISPLAY_C[1:] == "0." and key_name == ".":
                # First digit entry
                dp_flag = True
                DISPLAY_C = DISPLAY_C.replace("0.", key_name)
            elif DISPLAY_C[1:] == "0.":
                DISPLAY_C = DISPLAY_C.replace("0", key_name)
            else:
                dp_index = DISPLAY_C.index(".")
                if key_name != ".":
                    if dp_flag:
                        # Fractional portion (right of decimal separator)
                        DISPLAY_C = DISPLAY_C + key_name
                    else:
                        # Integer portion (left of decimal separator)
                        DISPLAY_C = (
                            DISPLAY_C[0:dp_index] + key_name + DISPLAY_C[dp_index:]
                        )
                else:
                    dp_flag = True

        if eex_flag and (key_name not in ("CHS", "EEX")):
            if DISPLAY_E[1:3] == "00":  # first digit entry
                DISPLAY_E = DISPLAY_E[0:2]+key_name
            elif DISPLAY_E[1] == "0":  # second digit entry
                DISPLAY_E = DISPLAY_E[0] + DISPLAY_E[2] + key_name

        if key_name == "CHS":
            if not eex_flag and DISPLAY_C[1:3] != "0.":
                if DISPLAY_C[0] == "-":
                    DISPLAY_C = " " + DISPLAY_C[1:]
                else:
                    DISPLAY_C = "-" + DISPLAY_C[1:]
            else:
                if DISPLAY_E[0] == "-":
                    DISPLAY_E = " " + DISPLAY_E[1:]
                else:
                    DISPLAY_E = "-" + DISPLAY_E[1:]
        if key_name == "EEX":
            eex_flag = True



        error_flag = False
        show_display_reg()
        update_x_reg()

    # Enter/Stack/Memory/Constant Key Cluster
    if key_name in (
        "ENTER",
        "CLR",
        "CLX",
        "STO",
        "RCL",
        "R",
        "x<>y",
        "π",
    ):
        # print("enter/stack/memory/constant key")
        digit_entry = False
        error_flag = False
        if key_name == "ENTER":
            push_stack()
            eex_flag = dp_flag = False
        if key_name == "CLR":
            clr()
            eex_flag = dp_flag = False
        if key_name == "CLX":
            clr("x")
            eex_flag = dp_flag = False
        if key_name == "STO":
            MEM = X_REG
        if key_name == "RCL":
            push_stack()
            X_REG = MEM
        if key_name == "R":
            roll_stack()
            eex_flag = dp_flag = False
        if key_name == "π":
            X_REG = Decimal("1.0").atan() * 4
            # X_REG = Decimal("3.141592654")

    # Monadic Operator Key Cluster
    if key_name in (
        "LOG",
        "LN",
        "e^x",
        "√x",
        "ARC",
        "SIN",
        "COS",
        "TAN",
        "1/x",
    ):
        # print("monadic operator key")
        digit_entry = False
        error_flag = False
        try:
            if key_name == "LOG":
                X_REG = Decimal.log10(X_REG)
            if key_name == "LN":
                X_REG = Decimal.ln(X_REG)
            if key_name == "e^x":
                X_REG = Decimal.exp(X_REG)
            if key_name == "√x":
                X_REG = Decimal.sqrt(X_REG)
            if key_name == "ARC":
                arc_flag = True
            if key_name == "SIN":
                if arc_flag:
                    X_REG = Decimal.asin(X_REG)
                else:
                    X_REG = Decimal.sin(X_REG)
                arc_flag = False
            if key_name == "COS":
                if arc_flag:
                    X_REG = Decimal.acos(X_REG)
                else:
                    X_REG = Decimal.cos(X_REG)
                arc_flag = False
            if key_name == "TAN":
                if arc_flag:
                    X_REG = Decimal.atan(X_REG)
                else:
                    X_REG = Decimal.tan(X_REG)
                arc_flag = False
            if key_name == "1/x":
                X_REG = 1 / X_REG
        except Exception as err:
            print("Exception:", err)
            display_error()
        if X_REG.is_infinite():
            print("Error: Infinite value in X_REG")
            display_error()

    # Diadic Operator Key Cluster
    if key_name in (
        "x^y",
        "x<>y",
        "-",
        "+",
        "*",
        "÷",
    ):
        # print("diadic operator key")
        digit_entry = False
        error_flag = False
        try:
            if key_name == "x^y":
                X_REG = X_REG ** Y_REG
            if key_name == "x<>y":
                temp = X_REG
                X_REG = Y_REG
                Y_REG = temp
            if key_name == "-":
                Y_REG = Y_REG - X_REG
                pull_stack()
                automatic_entry = True
            if key_name == "+":
                Y_REG = Y_REG + X_REG
                pull_stack()
                automatic_entry = True
            if key_name == "*":
                Y_REG = Y_REG * X_REG
                pull_stack()
                automatic_entry = True
            if key_name == "÷":
                Y_REG = Y_REG / X_REG
                automatic_entry = True
                pull_stack()
        except Exception as err:
            print("Exception:", err)
            display_error()
        if X_REG.is_infinite() or Y_REG.is_infinite():
            print("Error: Infinite value in X_REG and/or Y_REG")
            display_error()

    if (not digit_entry) and (not error_flag):
        display_x_reg()

        gc.collect()  # Clean-up memory heap space
        print_stack()
        frame = time.monotonic() - t0
        free_memory = gc.mem_free()
        print(f"frame: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb")
