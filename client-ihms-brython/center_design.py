""" center_design """

import math

def stabbeur_center(x: int, y: int, ctx):  # pylint: disable=invalid-name
    """ display a center the stabbeur way """

    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * math.pi, False)
    ctx.fill(); ctx.stroke(); ctx.closePath()
