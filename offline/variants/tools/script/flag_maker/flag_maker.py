#!/usr/bin/env python3


"""
Make background color
"""

import argparse
import typing
import os
import sys
import json

from PIL import Image, ImageFont, ImageDraw, ImageEnhance



INSERT_POSITION = 5 # albania
INSERT_TYPE = 1 # coast


def makeflags(json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ background """

    # ----------
    # parameters
    # ----------

    # roles
    for role, role_data in json_parameters_data['roles'].items():
        if int(role) == 0:
            continue

        color_tuple = (role_data['red'][0], role_data['green'][0], role_data['blue'][0])
        new_img = Image.new('RGB', (37, 25), color=color_tuple)

        if sum(color_tuple) > 127 * 3:
            color_fill = (0,0,0)
        else:
            color_fill = (255,255,255)

        draw = ImageDraw.Draw(new_img)
        draw.text((0, 0), role_data['name'][:6], font=None, fill=color_fill)

        new_img.save(f"{role}.jpg", "JPEG")



def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file

    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with open(parameters_file, "r", encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    makeflags(json_parameters_data)


if __name__ == "__main__":
    main()
