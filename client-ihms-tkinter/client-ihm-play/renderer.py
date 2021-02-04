#!/usr/bin/env python3

"""
an ihm based on tkinter
This low level module holds the abstract Renderer class
"""

import abc


class Renderer(abc.ABC):
    """ Something that displays in canvas """

    @abc.abstractmethod
    def render(self) -> None:
        """ should render  """


if __name__ == "__main__":
    assert False, "Do not run this script directly"
