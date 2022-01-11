# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# rpn_calculator.py
# 2022-01-10 v0.810

# An HP-35 -like RPN calculator for the Adafruit PyPortal Titano

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

calculator.append(case_group)
calculator.append(x_reg_display)
calculator.append(buttons)


def clr(register=None):
    if register:
        print("clr(" + register + "):")
    else:
        print("clr:")
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
        return False
    return True



def get_key():
    #  Get pressed key name. This is a blocking method.
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
    print("130", "'"+coefficient+"'", len(coefficient))
    if coefficient[0] == ".":
        coefficient = "0" + coefficient
    print("133", "'"+coefficient+"'", len(coefficient))

    # Clean up and reformat exponent
    while exponent.find(" ") >= 0:
        exponent = exponent.split(" ", 1)[0] + exponent.split(" ", 1)[1]
    if exponent == "":
        exponent = "0"
    exponent = "E" + str(int(exponent))

    #print("-----")
    #print("     ","012345678901234")
    #print("text:", text)
    #print("sign, coefficient, exponent:", sign, coefficient, exponent)
    #print("sign+coefficient+exponent  :", sign + coefficient + exponent)
    print("147 Decimal:", Decimal(sign+coefficient+exponent))

    return Decimal(sign+coefficient+exponent)

def convert_decimal_to_display(value=Decimal(0)):
    """Convert a Decimal value into the equivalent display text."""
    value = value * Decimal("1.")  # Force value to getcontext.prec() value
    decimal_text = str(value)
    #print("value, decimal_text, len(decimal_text)", value, decimal_text, len(decimal_text))

    # Retain "-" as sign but replace "+" with " "
    if decimal_text[0] == "-":
        coefficient = decimal_text.split("E", 1)[0]
    else:
        coefficient = " " + decimal_text.split("E", 1)[0]

    print("163", "'"+coefficient+"'", len(coefficient))
    if coefficient.find(".") < 0 and len(coefficient) < 10:
        coefficient = coefficient + "."
    print("166", "'"+coefficient+"'", len(coefficient))

    # add trailing spaces to coefficient if needed
    #coefficient = coefficient + (" " * (12 - len(coefficient)))

    #if len(coefficient) > 12:
    if True:
        if coefficient[1:] != "0.":
            # remove leading zeros
            print("convert_decimal_to_display(): remove leading zeros")
            while coefficient.find(".") >1 and coefficient[1] == "0":
                coefficient = coefficient[0] + coefficient[2:]
                print("value, coefficient, len(coefficient)", value, coefficient, len(coefficient))

        # remove trailing zeros from coefficient
        print("convert_decimal_to_display(): remove TRAILING zeros")
        while coefficient.find(".") <= 12 and coefficient[-1] == "0":
            coefficient = coefficient[0:-1]
            print("value, coefficient, len(coefficient)", value, coefficient, len(coefficient))

    if decimal_text.find("E") < 0:
        exponent = "   "
    else:
        exponent = decimal_text.split("E", 1)[1]

    #print("text:", decimal_text, type(decimal_text), len(decimal_text))
    #print("sign:", sign, len(sign))
    #print("coefficient:", coefficient, len(coefficient))
    #print("exponent:", exponent, len(exponent))
    #print(coefficient + exponent, len(coefficient + exponent))
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

def update_x_reg():
    # Move DISPLAY registers' content to the X_REG
    global X_REG, DISPLAY_C, DISPLAY_E
    print("update x_reg()", "'" + DISPLAY_C + "' '" + DISPLAY_E + "'")
    X_REG = convert_display_to_decimal(DISPLAY_C, DISPLAY_E)
    return

def display_x_reg():
    # Update the LED display with X_REG value
    global X_REG
    print("display x_reg()", X_REG)
    coefficient, exponent = convert_decimal_to_display(X_REG)
    DISPLAY_C = coefficient
    DISPLAY_E = exponent
    coefficient = coefficient + (" " * (12 - len(coefficient)))  # If needed, pad coefficient with spaces
    x_reg_display.text = coefficient + exponent
    return

def conversion_test():
    # test cases => (display text --> Decimal value --> display text)
    TEST_CASES = [
        (" 0.            ", "0",                " 0.            "),
        (" 1.            ", "1",                " 1.            "),
        ("-1.            ", "-1",               "-1.            "),
        (" 123.          ", "123",              " 123.          "),
        ("-12.34567      ", "-12.34567",        "-12.34567      "),
        ("-.1234567800- 2",  "-0.001234567800", "-.0012345678   "),
        ("-1.234567890-20", "-1.234567890E-20", "-1.234567890-20"),
        (" 1234567890.  1",  "1.234567890E+10", " 1.234567890+10"),
        (" 0.98765    - 3",  "0.00098765",      " 0.00098765    "),

    ]
    while True:
        for i in TEST_CASES:
            a = i[0]
            b = convert_display_to_decimal(a[0:12], a[12:15])
            print("* display text:     -> Decimal value:      should be:")
            print(f"  '{a:15s}'    '{b}'{(16-len(str(b)))*" "}  '{i[1]}'{(16-len(str(i[1])))*" "}  {str(b) == i[1]}")
            c = convert_decimal_to_display(b)[0] + convert_decimal_to_display(b)[1]
            print("  Decimal value:    -> display text:       should be:")
            print(f"  '{b}'{(16-len(str(b)))*" "}   '{c:15s}'   '{i[2]}'{(16-len(str(i[2])))*" "}  {c == i[2]}")
            print()

        while True:
            pass


getcontext().prec = 10
getcontext().Emax = 99
getcontext().Emin = -99

#conversion_test()

display.show(calculator)

gc.collect()
free_memory = gc.mem_free()
frame = time.monotonic() - t0
x_reg_display.text = f"{frame:5.02f}    {free_memory/1000:6.03f}"
print("CG-35 Calculator")
print(f'setup: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb')
time.sleep(1)

arc_flag = False
eex_flag = False
dp_flag = False
operation_completed = True

clr()
display_x_reg()

while True:
    t0 = time.monotonic()

    key_name = get_key()

    # Digit Entry Keys Cluster
    if key_name in ("0","1","2","3","4","5","6","7","8","9",".",):
        print("digit entry key")
        if operation_completed:
            # Prepare for digit entry when previous operation has finished
            #DISPLAY_C = DISPLAY_C + (" " * (12 - len(DISPLAY_C)))
            #Y_REG = convert_display_to_decimal(DISPLAY_C, DISPLAY_E)

            clr("x")
            eex_flag = dp_flag = False
            operation_completed = False

        if len(DISPLAY_C) < 12:
            if DISPLAY_C[1:] == "0." and key_name == ".":
                # first digit entry
                dp_flag = True
                print("300 before", DISPLAY_C, len(DISPLAY_C))
                DISPLAY_C = DISPLAY_C.replace("0.", key_name)
                print("302 after", DISPLAY_C, len(DISPLAY_C))
            elif DISPLAY_C[1:] == "0.":
                DISPLAY_C = DISPLAY_C.replace("0", key_name)
            else:
                dp_index = DISPLAY_C.index(".")
                print("307", dp_flag, dp_index, DISPLAY_C, len(DISPLAY_C))
                if key_name != ".":
                    if dp_flag:
                        # Fractional portion (right of decimal separator)
                        DISPLAY_C = DISPLAY_C + key_name
                    else:
                        # Integer portion (left of decimal separator)
                        DISPLAY_C = DISPLAY_C[0:dp_index] + key_name + DISPLAY_C[dp_index:]
                else:
                    dp_flag = True
        update_x_reg()

    # Display Control Keys Cluster
    if key_name in ("CHS","CLX","EEX",):
        print('display control key')
        if key_name == "CLX":
            clr("x")
            eex_flag = dp_flag = False
            operation_completed = True
        if key_name == "CHS":
            if not eex_flag:
                X_REG = X_REG * -1
            else:
                if "-" in DISPLAY_E:
                    DISPLAY_E = DISPLAY_E.replace("-", " ")
                else:
                    DISPLAY_E = DISPLAY_E.replace(" ", "-")
        if key_name == "EEX":
            if not eex_flag:
                eex_flag = True

    # Enter/Stack/Memory/Constant Key Cluster
    if key_name in ("ENTER","CLR","STO","RCL", "R","x<>y","π",):
        print("enter/stack/memory/constant key")
        if key_name == "ENTER":
            print("enter", X_REG)
            push_stack()
            print(X_REG, Y_REG)
            eex_flag = dp_flag = False
            operation_completed = True
        if key_name == "CLR":
            clr()
            eex_flag = dp_flag = False
        if key_name == "STO":
            MEM = X_REG
            operation_completed = True
        if key_name == "RCL":
            X_REG = MEM
            operation_completed = False
        if key_name == "R":
            roll_stack()
            eex_flag = dp_flag = False
            operation_completed = True
        if key_name == "π":
            X_REG = Decimal("3.141592654").normalize()
            #X_REG = Decimal("1.0").atan() * 4
            operation_completed = True

    # Monadic Operator Key Cluster
    if key_name in ("LOG","LN","e^x","√x","ARC","SIN","COS","TAN","1/x",):
        print("monadic operator key")
        if key_name == "LOG":
            X_REG = Decimal.log10(X_REG).normalize()
            operation_completed = True
        if key_name == "LN":
            # check for error: can't derive the ln from a negative number
            X_REG = Decimal.ln(X_REG).normalize()
            operation_completed = True
        if key_name == "e^x":
            # check for errors
            X_REG = Decimal.exp(X_REG).normalize()
            operation_completed = True
        if key_name == "√x":
            X_REG = Decimal.sqrt(X_REG).normalize()
            operation_completed = True
        if key_name == "ARC":
            arc_flag = True
        if key_name == "SIN":
            if arc_flag:
                X_REG = Decimal.asin(X_REG).normalize()
            else:
                X_REG = Decimal.sin(X_REG).normalize()
            arc_flag = False
            operation_completed = True
        if key_name == "COS":
            if arc_flag:
                X_REG = Decimal.acos(X_REG).normalize()
            else:
                X_REG = Decimal.cos(X_REG).normalize()
            arc_flag = False
            operation_completed = True
        if key_name == "TAN":
            if arc_flag:
                X_REG = Decimal.atan(X_REG).normalize()
            else:
                X_REG = Decimal.tan(X_REG).normalize()
            arc_flag = False
            operation_completed = True
        if key_name == "1/x":
            # Check for ERROR: divide by zero
            X_REG = (1 / X_REG).normalize()
            operation_completed = True

    # Diadic Operator Key Cluster
    if key_name in ("x^y","x<>y","-","+","*","÷",):
        print("diadic operator key")
        if key_name == "x^y":
            X_REG = X_REG ** Y_REG
            operation_completed = True
        if key_name == "x<>y":
            temp = X_REG
            X_REG = Y_REG
            Y_REG = temp
            operation_completed = True
        if key_name == "-":
            Y_REG = (Y_REG - X_REG).normalize()
            pull_stack()
            operation_completed = True
        if key_name == "+":
            Y_REG = (Y_REG + X_REG).normalize()
            pull_stack()
            operation_completed = True
        if key_name == "*":
            Y_REG = (Y_REG * X_REG).normalize()
            pull_stack()
            operation_completed = True
        if key_name == "÷":
            Y_REG = (Y_REG / X_REG).normalize()
            pull_stack()
            operation_completed = True


    display_x_reg()
    gc.collect()

    if operation_completed:
        print_stack()
        frame = time.monotonic() - t0
        free_memory = gc.mem_free()
        print(f'frame: {frame:5.02f}sec   free memory: {free_memory/1000:6.03f}kb')
