# SPDX-FileCopyrightText: 2022 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
cg_35_calculator.py  2022-02-16 v0.0216 ALPHA
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
    - fix Decimal to display formatting and rounding
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
from cedargrove_calculator.case import CalculatorCase, LEDDisplay
from cedargrove_widgets.bubble_display import BubbleDisplay

from jepler_udecimal import Decimal, getcontext, setcontext, localcontext, ROUND_HALF_UP
import jepler_udecimal.utrig  # Needed for trig functions in Decimal

# user-modifiable parameters
VISIBLE_CASE = True
DISPLAY_PRECISION  = 10
INTERNAL_PRECISION = 20

DEBUG = True  # Turns on 'printd' function

# Calculator states
IDLE    = "IDLE"     # Waiting for input or displaying results
C_ENTRY = "C_ENTRY"  # Coefficient entry: 0-9, ., CHS, EEX
E_ENTRY = "E_ENTRY"  # Exponent entry: 0-9, ., CHS
STACK   = "STACK"    # Stack management: ENTER, CLR, CLX, STO, RCL, R, x<>y, π
MONADIC = "MONADIC"  # Monadic operatation: LOG, LN, e^x, √x, ARC, SIN, COS, ,TAN, 1/x
DIADIC  = "DIADIC"   # Diadic operation: x^y, -, +, *, ÷
ERROR   = "ERROR"    # Calculation error

STATE = IDLE  # Set initial state to IDLE

# Constants
PI = Decimal(1).atan() * 4  # Alternative: PI = Decimal("3.141592654")

t0 = time.monotonic()  # Reset start-up time counter
gc.collect()  # Clean-up memory heap space

# Create the primary displayio.Group layer
calculator = displayio.Group()

# Rotate the display to portrait orientation
display = board.DISPLAY
display.rotation = 90
display.brightness = 1.0  # Titano: 0.55 for camera image

# Instatiate case group and buttons class
case_group = CalculatorCase(visible=VISIBLE_CASE)
buttons = CalculatorButtons(
    l_margin=case_group.l_margin, timeout=10, click=True
)
led_display = LEDDisplay(scale=1)

"""# Instantiate the BubbleDisplay widget: 15-digit display, dedicated decimal point
led_display = BubbleDisplay(
    units=5, digits=3, mode="HP-35", center=(0.5, 0.08), size=0.58
)"""

gc.collect()  # Clean-up memory heap space

# Sets the default internal precision and exponent range
getcontext().prec = INTERNAL_PRECISION
getcontext().Emax = 99
getcontext().Emin = -99
#getcontext().rounding = ROUND_HALF_UP

# Initiate the display, memory, and stack
DISPLAY_C = " 0."
DISPLAY_E = " 00"
X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")

# Add the case, bubble display, and button displayio layers
calculator.append(case_group)
calculator.append(led_display)
calculator.append(buttons)

def printd(line):
    if DEBUG:
        print(line)
    return

def clr(register=None):
    """Clear the display and all or just X_REG; None for all registers; "x" for X_REG."""
    global DISPLAY_C, DISPLAY_E, X_REG, Y_REG, Z_REG, T_REG, MEM, ARC_FLAG
    if not register:
        # Clear display, stack registers, memory, and reset ARC flag
        DISPLAY_C = " 0."
        DISPLAY_E = " 00"
        X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")
        ARC_FLAG = False
    elif register == "x":
        # Clear display and X_REG
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
    # printd(f"get_key: name:{key_name:5s} hold_time:{hold_time:5.3f}s")
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
    printd(f"display_to_decimal in: '{coefficient}'  '{exponent}'")
    getcontext().prec = DISPLAY_PRECISION
    sign = coefficient[0]
    coefficient = coefficient[1:12]
    exponent = exponent[0:3]

    # Reformat sign for decimal value conversion
    if sign == " ":
        sign = "+"

    # Clean up and reformat coefficient; remove spaces, put zero before dp if dp is in first position
    while coefficient.find(" ") >= 0:
        coefficient = coefficient.split(" ", 1)[0] + coefficient.split(" ", 1)[1]
    if coefficient[0] == ".":
        coefficient = "0" + coefficient
    for i in range(len(coefficient), getcontext().prec + 1):  # pad coefficient with trailing zeros for values with positive exponent
        coefficient = coefficient + "0"

    # How do we preface coefficient values < 1.0 (negative exponent) so that they convert properly?

    # Clean up and reformat exponent; remove spaces, set to zero if blank, add separator E character
    while exponent.find(" ") >= 0:
        exponent = exponent.split(" ", 1)[0] + exponent.split(" ", 1)[1]
    if exponent == "":
        exponent = "0"
    exponent = "E" + str(int(exponent))

    new_value = Decimal(sign + coefficient + exponent)   # Reconstruct the value as Decimal type

    getcontext().prec = INTERNAL_PRECISION
    new_value = new_value / 1

    printd(f"display_to_decimal: new_value out: '{new_value}'")
    return new_value


def convert_decimal_to_display(value=Decimal("0")):
    """Convert a Decimal value into the equivalent display text."""
    # Round to display precision and convert to string
    #printd(f"decimal_to_display value in: '{value}'  type: {type(value)}")
    if value.is_finite():
        value = value / 1
        getcontext().prec = DISPLAY_PRECISION
        value = value / 1
    else:
        value = Decimal(0)

    # DO SOME NORMALIZATION HERE

    #printd(f"decimal_to_display: value.adjusted() = '{value.adjusted()}'")

    decimal_text = str(value)
    #printd(f"decimal_to_display: decimal_text= '{decimal_text}'  value= '{value}'")

    # Separate coefficient from exponent
    if decimal_text.find("E") >=0:
        coefficient, exponent = decimal_text.split("E", 1)
    else:
        coefficient = decimal_text
        exponent = " 00"

    #printd(f"* coefficient '{coefficient}', exponent '{exponent}'")
    #printd(f"  len(coefficient):{len(coefficient)}, len(exponent):{len(exponent)}")

    # Coefficient: Retain "-" as sign; add " " for positive value
    if coefficient[0] != "-":
        coefficient = " " + coefficient

    # Exponent: Replace + with space; retain minus sign
    if exponent[0] == "+":  # if plus sign, replace with space
        exponent = (" " * (4 -len(exponent))) + exponent[1:]
    if exponent[0] == "-" and len(exponent) == 2:
        exponent = "- " + exponent[-1]

    #printd(f"** coefficient '{coefficient}', exponent '{exponent}'")
    #printd(f"   len(coefficient):{len(coefficient)}, len(exponent):{len(exponent)}")

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

    #printd(f"*** coefficient '{coefficient}', exponent '{exponent}'")
    #printd(f"    len(coefficient):{len(coefficient)}, len(exponent):{len(exponent)}")

    # If no exponent separator or coefficient is zero, blank the exponent value
    if decimal_text.find("E") < 0 or coefficient[1:] == "0.":
        exponent = "   "

    #printd(f"**** coefficient '{coefficient}', exponent '{exponent}'")
    #printd(f"     len(coefficient):{len(coefficient)}, len(exponent):{len(exponent)}")

    getcontext().prec = INTERNAL_PRECISION

    return coefficient, exponent

def print_stack():
    """Print stack registers and auxillary memory."""
    print(f"-" * 48)
    print(
        f"D.X_REG:  {X_REG}  DISPLAY: '{convert_decimal_to_display(X_REG)[0] + convert_decimal_to_display(X_REG)[1]}'"
    )
    print(f"D.Y_REG:  {Y_REG}")
    print(f"D.Z_REG:  {Z_REG}")
    print(f"D.T_REG:  {T_REG}")
    print(f"D.MEM  :  {MEM}")
    print(f"-" * 48)
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

def display_error(text=""):
    """Flash error indicator on display."""
    global STATE, ERROR
    STATE = ERROR
    clr()
    led_display.text = "." * 15
    time.sleep(0.2)
    led_display.text = " " * 15
    time.sleep(0.2)
    led_display.text = "." * 15
    display_status(text, None)
    return

def display_status(text="", duration=0.5):
    """Display message in status area for duration in seconds."""
    case_group.status.text = text
    if duration:
        time.sleep(duration)
        case_group.status.text = ""
    return

def update_x_reg_from_display_reg():
    """Move DISPLAY registers' content to the X_REG."""
    global X_REG, DISPLAY_C, DISPLAY_E
    if DISPLAY_E == "-00":
        DISPLAY_E = " 00"
    X_REG = convert_display_to_decimal(DISPLAY_C, DISPLAY_E)
    return

def update_display_reg_from_x_reg():
    """Update the LED display with X_REG value."""
    global X_REG, DISPLAY_C, DISPLAY_E
    coefficient, exponent = convert_decimal_to_display(X_REG)
    DISPLAY_C = coefficient
    DISPLAY_E = exponent
    # If needed, pad coefficient with spaces
    coefficient = coefficient + (" " * (12 - len(coefficient)))
    led_display.text = coefficient + exponent
    return

def convert_degrees_to_radians(value):
    """Convert Decimal degrees value to radians."""
    return (value % 360) * (PI * 2) / 360

def convert_radians_to_degrees(value):
    """Convert Decimal radians value to degrees."""
    return (value % (PI * 2)) * 360 / (PI * 2)


display.show(calculator)

gc.collect()
free_memory = gc.mem_free()
frame = time.monotonic() - t0
print("CG-35 Calculator    Cedar Grove Studios")
print(f"setup: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb")
print(f"Calculator STATE: {STATE}")
display_status("... READY ...", 1)

clr()
update_display_reg_from_x_reg()

while True:
    t0 = time.monotonic()  # Reset timer for start of frame

    key_name = get_key()  # Wait for key press
    display_status("", 0)  # Clear any status messages

    # Display Entry Keys Cluster: 0-9, ., CHS, EEX
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
        printd(f"Display entry key: {key_name}")
        if not "ENTRY" in STATE:
            # Prepare for digit entry when previous operation has finished
            if STATE == DIADIC:
                push_stack()  #  Automatic ENTER only after diadic operations
            clr("x")
            dp_flag = False
            STATE = C_ENTRY

        if (STATE == C_ENTRY) and (STATE != E_ENTRY) and len(DISPLAY_C) < 12 and (key_name not in ("CHS", "EEX")):
            getcontext().prec = DISPLAY_PRECISION
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
                        # Fractional portion of coefficient (right of decimal separator)
                        DISPLAY_C = DISPLAY_C + key_name
                    else:
                        # Integer portion of coefficient (left of decimal separator)
                        DISPLAY_C = (
                            DISPLAY_C[0:dp_index] + key_name + DISPLAY_C[dp_index:]
                        )
                else:
                    dp_flag = True

        if (STATE == E_ENTRY) and (key_name not in ("CHS", "EEX")):
            if DISPLAY_E[1:3] == "00":  # first digit entry
                DISPLAY_E = DISPLAY_E[0:2]+key_name
            elif DISPLAY_E[1] == "0":  # second digit entry
                DISPLAY_E = DISPLAY_E[0] + DISPLAY_E[2] + key_name

        if key_name == "CHS":
            if (STATE == C_ENTRY) and DISPLAY_C[1:3] != "0.":
                # change the coefficient sign
                if DISPLAY_C[0] == "-":
                    DISPLAY_C = " " + DISPLAY_C[1:]
                else:
                    DISPLAY_C = "-" + DISPLAY_C[1:]
            elif STATE == E_ENTRY:
                # change the exponent sign
                if DISPLAY_E[0] == "-":
                    DISPLAY_E = " " + DISPLAY_E[1:]
                else:
                    DISPLAY_E = "-" + DISPLAY_E[1:]

        if key_name == "EEX":
            STATE = E_ENTRY

        show_display_reg()
        update_x_reg_from_display_reg()

    # Stack Management and Constant Key Cluster: ENTER, CLR, CLX, STO, RCL, R, x<>y, π
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
        STATE = STACK
        printd(f"stack management and constant key: {key_name}")
        if key_name == "ENTER":
            push_stack()
        if key_name == "CLR":
            clr()
        if key_name == "CLX":
            clr("x")
        if key_name == "STO":
            MEM = X_REG
        if key_name == "RCL":
            push_stack()
            X_REG = MEM
        if key_name == "R":
            roll_stack()
        if key_name == "x<>y":
            temp = X_REG
            X_REG = Y_REG
            Y_REG = temp
        if key_name == "π":
            X_REG = PI

    # Monadic Operator Key Cluster: LOG, LN, e^x, √x, ARC, SIN, COS, ,TAN, 1/x
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
        STATE = MONADIC
        printd(f"monadic operator key: {key_name}")
        try:
            getcontext().prec = INTERNAL_PRECISION
            if key_name == "LOG":
                X_REG = Decimal.log10(X_REG)
            if key_name == "LN":
                X_REG = Decimal.ln(X_REG)
            if key_name == "e^x":
                X_REG = Decimal.exp(X_REG)
            if key_name == "√x":
                X_REG = Decimal.sqrt(X_REG)
            if key_name == "ARC":
                ARC_FLAG = True
            if key_name == "SIN":
                if ARC_FLAG:
                    X_REG = convert_radians_to_degrees(Decimal.asin(X_REG))
                else:
                    X_REG = Decimal.sin(convert_degrees_to_radians(X_REG))
                ARC_FLAG = False
            if key_name == "COS":
                if ARC_FLAG:
                    X_REG = convert_radians_to_degrees(Decimal.acos(X_REG))
                else:
                    X_REG = Decimal.cos(convert_degrees_to_radians(X_REG))
                ARC_FLAG = False
            if key_name == "TAN":
                if ARC_FLAG:
                    X_REG = convert_radians_to_degrees(Decimal.atan(X_REG))
                else:
                    X_REG = Decimal.tan(convert_degrees_to_radians(X_REG))
                ARC_FLAG = False
            if key_name == "1/x":
                X_REG = 1 / X_REG
        except Exception as err:
            print("Exception:", err)
            display_error(str(type(err))[8:-2])
        if X_REG.is_infinite():
            print("Error: Infinite value in X_REG")
            display_error("Infinite value in X_REG")

    # Diadic Operator Key Cluster: x^y, -, +, *, ÷
    if key_name in (
        "x^y",
        "-",
        "+",
        "*",
        "÷",
    ):
        STATE = DIADIC
        printd(f"diadic operator key: {key_name}")
        try:
            getcontext().prec = INTERNAL_PRECISION
            if key_name == "x^y":
                X_REG = X_REG ** Y_REG
            if key_name == "-":
                Y_REG = Y_REG - X_REG
                pull_stack()
            if key_name == "+":
                Y_REG = Y_REG + X_REG
                pull_stack()
            if key_name == "*":
                Y_REG = Y_REG * X_REG
                pull_stack()
            if key_name == "÷":
                Y_REG = Y_REG / X_REG
                pull_stack()
        except Exception as err:
            print("Exception:", err)
            display_error(str(type(err))[8:-2])
        if X_REG.is_infinite() or Y_REG.is_infinite():
            print("Error: Infinite value in X_REG and/or Y_REG")
            display_error("Infinite value in X_REG")

    if STATE not in ("C_ENTRY", "E_ENTRY", "ERROR"):
        STATE = IDLE
        update_display_reg_from_x_reg()
        gc.collect()  # Clean-up memory heap space
        print_stack()
        frame = time.monotonic() - t0
        free_memory = gc.mem_free()
        print(f"frame: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb")
        print(f"Calculator STATE: {STATE}")
