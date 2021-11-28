""" center_design """

# pylint: disable=multiple-statements

import math


CENTER_RAY = 5


def stabbeur_center(x: int, y: int, ctx):  # pylint: disable=invalid-name
    """ display a center the stabbeur way """

    ctx.beginPath()
    ctx.arc(x, y, CENTER_RAY, 0, 2 * math.pi, False)
    ctx.fill(); ctx.stroke(); ctx.closePath()
