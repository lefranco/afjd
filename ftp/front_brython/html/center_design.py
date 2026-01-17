""" center_design """

# pylint: disable=multiple-statements

from math import pi


CENTER_RAY = 5


def stabbeur_center(x: int, y: int, ctx):  # pylint: disable=invalid-name
    """ display a center the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined
    ctx.lineWidth = 1

    ctx.beginPath()
    ctx.arc(x, y, CENTER_RAY, 0, 2 * pi, False)
    ctx.fill(); ctx.stroke(); ctx.closePath()
