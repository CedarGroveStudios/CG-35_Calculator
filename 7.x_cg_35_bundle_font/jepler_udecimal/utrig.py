#!/usr/bin/env python3
# -*- utf-8 -*-
# SPDX-FileCopyrightText: 2020 Jeff Epler <https://unpythonic.net>
#
# SPDX-License-Identifier: BSD-2-Clause
#
# Adapted from https://git.yzena.com/gavin/bc/src/branch/master/gen/lib.bc
# which states: SPDX-License-Identifier: BSD-2-Clause
#
# Copyright (c) 2018-2020 Gavin D. Howard and contributors.
#
# The algorithms use range reductions and taylor polynomaials

# pylint: disable=invalid-name,protected-access

"""
Trig functions using jepler_udecimal

Importing this module adds the relevant methods to the `Decimal` object.

Generally speaking, these routines increase the precision by some amount,
perform argument range reduction followed by evaluation of a taylor polynomial,
then reduce the precision of the result to equal the origial context's
precision.

There is no guarantee that the results are correctly rounded in all cases,
however, in all but the rarest cases the digits except the last one can be
trusted.

Here are some examples of using utrig:

>>> import jepler_udecimal.utrig
>>> from jepler_udecimal import Decimal
>>> Decimal('.7').atan()
Decimal('0.6107259643892086165437588765')
>>> Decimal('.1').acos()
Decimal('1.470628905633336822885798512')
>>> Decimal('-.1').asin()
Decimal('-0.1001674211615597963455231795')
>>> Decimal('.4').tan()
Decimal('0.4227932187381617619816354272')
>>> Decimal('.5').cos()
Decimal('0.8775825618903727161162815826')
>>> Decimal('.6').sin()
Decimal('0.5646424733950353572009454457')
>>> Decimal('1').asin()
Decimal('1.570796326794896619231321692')
>>> Decimal('-1').acos()
Decimal('3.141592653589793238462643383')


"""

from . import Decimal, localcontext, getcontext, InvalidOperation

__all__ = ["acos", "asin", "atan", "cos", "sin", "tan"]

_point2 = Decimal(".2")


def atan(x, context=None):
    """Compute the arctangent of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    with localcontext(context) as ctx:
        scale = ctx.prec

        n = 1
        if x < 0:
            n = -1
            x = -x

        # Hard code values for inputs +-1 and +-.2
        if scale < 65:
            if x == 1:
                return (
                    Decimal(
                        ".7853981633974483096156608458198757210492923498437764552437361480"
                    )
                    / n
                )
            if x == _point2:
                return (
                    Decimal(
                        ".1973955598498807583700497651947902934475851037878521015176889402"
                    )
                    / n
                )

        if x > _point2:
            ctx.prec += 5
            a = atan(_point2)
        else:
            a = 0

        ctx.prec = scale + 3

        # This very efficient range reduction reduces 1e300 to under .2 in
        # just 6 iterations!
        m = 0
        while x > _point2:
            m += 1
            x = (x - _point2) / (1 + _point2 * x)

        r = u = x
        f = -x * x
        t = Decimal(1)
        i = 3

        while t and t.logb() > -ctx.prec:
            u *= f
            t = u / i
            i += 2
            r += t

        r += m * a
    return r / n


def sin(x, context=None):
    """Compute the sine of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    with localcontext(context) as ctx:
        if x < 0:
            return -sin(-x)

        scale = ctx.prec

        ctx.prec = int(1.1 * scale + 2)
        a = atan(1)
        q = (x // a + 2) // 4
        x -= 4 * q * a
        if q % 2:
            x = -x
        ctx.prec = scale + 2
        r = a = x
        q = -x * x
        i = 3
        while a and a.logb() > -ctx.prec:
            a *= q / (i * (i - 1))
            r += a
            i += 2

    return r / 1


def cos(x, context=None):
    """Compute the cosine of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    with localcontext(context) as ctx:
        scale = ctx.prec
        ctx.prec = int(scale * 1.2)
        r = sin(2 * atan(1) + x)
    return r / 1


def tan(x, context=None):
    """Compute the tangent of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    with localcontext(context) as ctx:
        ctx.prec += 2
        s = sin(x)
        r = s / (1 - s * s).sqrt()
    return r / 1


def asin(x, context=None):
    """Compute the arcsine of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    context = context or getcontext()

    if x.compare_total_mag(Decimal(1)) > 0:
        return context._raise_error(InvalidOperation, "asin(x), |x| > 1")

    with localcontext(context) as ctx:
        ctx.prec += 2
        if x == 1:
            r = atan(Decimal(1)) * 2  # pi * 1/2 radians
        elif x == -1:
            r = atan(Decimal(1)) * -2  # pi * -1/2 radians
        else:
            r = atan(x / (1 - x * x).sqrt())
    return r / 1


def acos(x, context=None):
    """Compute the arccosine of the specified value, in radians"""
    if not isinstance(x, Decimal):
        x = Decimal(x)

    ans = x._check_nans(context=context)
    if ans:
        return ans

    context = context or getcontext()

    if x.compare_total_mag(Decimal(1)) > 0:
        return context._raise_error(InvalidOperation, "acos(x), |x| > 1")

    with localcontext(context) as ctx:
        ctx.prec += 2
        if x == 1:
            r = Decimal(0)  # 0 radians
        elif x == -1:
            r = atan(Decimal(1)) * 4  # pi radians
        else:
            r = atan((1 - x * x).sqrt() / x)
        if r < 0:
            r += 4 * atan(1)
    return r / 1


for name in __all__:
    setattr(Decimal, name, globals()[name])
