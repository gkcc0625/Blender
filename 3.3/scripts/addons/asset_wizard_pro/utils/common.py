# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

from math import floor, log
from mathutils import Vector


def clamp(v, mn, mx):
    """
    clamp v between mn and mx.
    """
    return max(mn, min(v, mx))


def round_next(value: float, snap: float) -> float:
    """
    Round value to snap sized grid.
    """
    if snap < 0.000001:
        return value

    reciprocal = 1 / snap
    val = round(value * reciprocal)
    return val / reciprocal


def round_next_vector(value: Vector, snap: float) -> Vector:
    """
    Round value to snap sized grid.
    """
    return Vector((
        round_next(value[0], snap),
        round_next(value[1], snap),
        round_next(value[2], snap)
    ))


def format_bytes(size):
    """
    Quick convert large numbers into prefix notation.
    """
    power = 0 if size <= 0 else floor(log(size, 1024))
    return f"{round(size / 1024 ** power, 2)} {['B', 'KB', 'MB', 'GB', 'TB'][int(power)]}"   


