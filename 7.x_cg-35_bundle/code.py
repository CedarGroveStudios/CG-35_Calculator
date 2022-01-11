# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# rpn_calculator.py
# 2022-01-11 v0.811

# An HP-35 -like RPN calculator for the Adafruit PyPortal Titano
# 10-digit display with 20-digit precision

import board
import displayio
import time
import gc
gc.collect()  # Clean-up memory heap space

from cedargrove_calculator.buttons_pyportal import CalculatorButtons
from cedargrove_calculator.case import CalculatorCase
from cedargrove_widgets.bubble_display import BubbleDisplay
#from cedargrove_sdcard import SDCard
from jepler_udecimal import Decimal, getcontext, setcontext, localcontext
import jepler_udecimal.utrig  # Needed for trig functions in Decimal

# To calibrate the touchscreeen, change calibrate=False to calibrate=True
# Enter new calibration settings in cedargrove_calculator.buttons_pyportal.py
CALIBRATE = False

t0 = time.monotonic()  # Reset start-up time counter
gc.collect()  # Clean-up memory heap space
#sdcard = SDCard()

# Create the primary displayio.Group layer
calculator = displayio.Group()

# Rotate the display; portrait mode
display = board.DISPLAY
display.rotation = 90
display.brightness = 1.0  # Titano: 0.55 max for camera image

# Instatiate case group and buttons class
case_group = CalculatorCase()

buttons = CalculatorButtons(l_margin=case_group.l_margin, timeout=10, calibrate=CALIBRATE, click=True)

# Instantiate the BubbleDisplay widget
x_reg_display = BubbleDisplay(
    units=5, digits=3, mode="HP-35", center=(0.5, 0.08), size=0.58
)
WIDTH = x_reg_display.display_size[0]
HEIGHT = x_reg_display.display_size[1]

DISPLAY_C = " 0."
DISPLAY_E = " 00"
X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")

getcontext().prec = 20
getcontext().Emax = 99
getcontext().Emin = -99

calculator.append(case_group)
calculator.append(x_reg_display)
calculator.append(buttons)


def clr(register=None):
    global DISPLAY_C, DISPLAY_E, X_REG, Y_REG, Z_REG, T_REG, MEM
    if not register:
        # Clear all registers
        DISPLAY_C = " 0."
        DISPLAY_E = " 00"
        X_REG = Y_REG = Z_REG = T_REG = MEM = Decimal("0")
    elif register == "x":
        DISPLAY_C = " 0."
        DISPLAY_E = " 00"
        X_REG = Decimal("0")
    else:
        # no register specified
        return False
    return True


def get_key():
    #  Get pressed key name. This is currently a blocking method.
    key_name = None
    while not key_name:
        key_name, _, hold_time = buttons.read_buttons()
    #print(f"get_key: name:{key_name:5s} hold_time:{hold_time:5.3f}s")
    return key_name

def push_stack():
    # push display value into the stack; T is lost
    global X_REG, Y_REG, Z_REG, T_REG
    T_REG = Z_REG
    Z_REG = Y_REG
    Y_REG = X_REG
    return

def pull_stack():
    # pull (drop) Y into X, Z into Y, and T into Z; "0" into T
    global X_REG, Y_REG, Z_REG, T_REG
    X_REG = Y_REG
    Y_REG = Z_REG
    Z_REG = T_REG
    T_REG = Decimal("0")
    return

def roll_stack():
    # roll stack values
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

    return Decimal(sign+coefficient+exponent)

def convert_decimal_to_display(value=Decimal(0)):
    """Convert a Decimal value into the equivalent display text."""
    value = value * Decimal("1.")  # Force value to getcontext.prec() value
    decimal_text = str(value.quantize(Decimal("1.000000000")).normalize())[0:12]

    # Retain "-" as sign but replace "+" with " "
    if decimal_text[0] == "-":
        coefficient = decimal_text.split("E", 1)[0]
    else:
        coefficient = " " + decimal_text.split("E", 1)[0]
    # place a decimal point in tenth digit position if possible
    if coefficient.find(".") < 0 and len(coefficient) < 10:
        coefficient = coefficient + "."
    # remove leading zeros except at start of digit entry
    if coefficient[1:] != "0.":
        while coefficient.find(".") >1 and coefficient[1] == "0":
            coefficient = coefficient[0] + coefficient[2:]
    # remove trailing zeros from coefficient
    while coefficient.find(".") <= 12 and coefficient[-1] == "0":
        coefficient = coefficient[0:-1]
    # don't display minus zero
    if coefficient == "-0.":
        coefficient = " 0."

    if decimal_text.find("E") < 0:
        exponent = "   "
    else:
        exponent = decimal_text.split("E", 1)[1]
    return coefficient, exponent


def print_stack():
    # print all stack registers
    print(f"D.X_REG:  {X_REG}  DISPLAY: '{convert_decimal_to_display(X_REG)[0] + convert_decimal_to_display(X_REG)[1]}'")
    print(f"D.Y_REG:  {Y_REG}")
    print(f"D.Z_REG:  {Z_REG}")
    print(f"D.T_REG:  {T_REG}")
    print()
    print(f"D.MEM  :  {MEM}")
    return


def display_display_reg():
    # Display contents of DISPLAY registers
    global DISPLAY_C, DISPLAY_E
    coefficient = DISPLAY_C
    exponent = DISPLAY_E
    if exponent[1:3] == "00":
        exponent = "   "
    coefficient = coefficient + (" " * (12 - len(coefficient)))  # If needed, pad coefficient with spaces
    x_reg_display.text = coefficient + exponent
    return


def update_x_reg():
    # Move DISPLAY registers' content to the X_REG
    global X_REG, DISPLAY_C, DISPLAY_E
    X_REG = convert_display_to_decimal(DISPLAY_C, DISPLAY_E)
    return


def display_x_reg():
    # Update the LED display with X_REG value
    global X_REG
    coefficient, exponent = convert_decimal_to_display(X_REG)
    DISPLAY_C = coefficient
    DISPLAY_E = exponent
    coefficient = coefficient + (" " * (12 - len(coefficient)))  # If needed, pad coefficient with spaces
    x_reg_display.text = coefficient + exponent
    return


display.show(calculator)

gc.collect()
free_memory = gc.mem_free()
frame = time.monotonic() - t0
x_reg_display.text = f"{frame:5.02f}    {free_memory/1000:6.03f}"
print("CG-35 Calculator    Cedar Grove Studios")
print(f'setup: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb')
time.sleep(1)

arc_flag = False
eex_flag = False
dp_flag = False
digit_entry_mode = False

clr()
display_x_reg()

while True:
    t0 = time.monotonic()

    key_name = get_key()

    # Display Entry Keys Cluster
    if key_name in ("0","1","2","3","4","5","6","7","8","9",".","CHS","EEX",):
        #print("display entry key", "digit entry mode:", digit_entry_mode)
        if not digit_entry_mode:
            # Prepare for digit entry when previous operation has finished
            clr("x")
            eex_flag = dp_flag = False
            digit_entry_mode = True

        if digit_entry_mode and len(DISPLAY_C) < 12 and (key_name not in ("CHS","EEX")):
            if DISPLAY_C[1:] == "0." and key_name == ".":
                # first digit entry
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
                        DISPLAY_C = DISPLAY_C[0:dp_index] + key_name + DISPLAY_C[dp_index:]
                else:
                    dp_flag = True
        if key_name == "CHS":
            if not eex_flag:
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
            if not eex_flag:
                eex_flag = True

        display_display_reg()
        update_x_reg()

    # Enter/Stack/Memory/Constant Key Cluster
    if key_name in ("ENTER","CLR","CLX","STO","RCL", "R","x<>y","π",):
        #print("enter/stack/memory/constant key")
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
            X_REG = MEM
        if key_name == "R":
            roll_stack()
            eex_flag = dp_flag = False
        if key_name == "π":
            #X_REG = Decimal("3.141592654").normalize()
            X_REG = (Decimal("1.0").atan() * 4).normalize()
            #X_REG = (Decimal("1.0").atan() * 4).quantize(Decimal("1.000000000"))
        digit_entry_mode = False

    # Monadic Operator Key Cluster
    if key_name in ("LOG","LN","e^x","√x","ARC","SIN","COS","TAN","1/x",):
        #print("monadic operator key")
        if key_name == "LOG":
            X_REG = Decimal.log10(X_REG).normalize()
        if key_name == "LN":
            # check for error: can't derive the ln from a negative number
            X_REG = Decimal.ln(X_REG).normalize()
        if key_name == "e^x":
            # check for errors
            X_REG = Decimal.exp(X_REG).normalize()
        if key_name == "√x":
            X_REG = Decimal.sqrt(X_REG).normalize()
        if key_name == "ARC":
            arc_flag = True
        if key_name == "SIN":
            if arc_flag:
                X_REG = Decimal.asin(X_REG).normalize()
            else:
                X_REG = Decimal.sin(X_REG).normalize()
            arc_flag = False
        if key_name == "COS":
            if arc_flag:
                X_REG = Decimal.acos(X_REG).normalize()
            else:
                X_REG = Decimal.cos(X_REG).normalize()
            arc_flag = False
        if key_name == "TAN":
            if arc_flag:
                X_REG = Decimal.atan(X_REG).normalize()
            else:
                X_REG = Decimal.tan(X_REG).normalize()
            arc_flag = False
        if key_name == "1/x":
            # Check for ERROR: divide by zero
            X_REG = (1 / X_REG).normalize()
        digit_entry_mode = False

    # Diadic Operator Key Cluster
    if key_name in ("x^y","x<>y","-","+","*","÷",):
        #print("diadic operator key")
        if key_name == "x^y":
            X_REG = (X_REG ** Y_REG).normalize()
        if key_name == "x<>y":
            temp = X_REG
            X_REG = Y_REG
            Y_REG = temp
        if key_name == "-":
            Y_REG = (Y_REG - X_REG).normalize()
            pull_stack()
        if key_name == "+":
            Y_REG = (Y_REG + X_REG).normalize()
            pull_stack()
        if key_name == "*":
            Y_REG = (Y_REG * X_REG).normalize()
            pull_stack()
        if key_name == "÷":
            Y_REG = (Y_REG / X_REG).normalize()
            pull_stack()
        digit_entry_mode = False

    if not digit_entry_mode:
        display_x_reg()

        gc.collect()  # Clean-up memory heap space
        print_stack()
        frame = time.monotonic() - t0
        free_memory = gc.mem_free()
        print(f'frame: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb')
