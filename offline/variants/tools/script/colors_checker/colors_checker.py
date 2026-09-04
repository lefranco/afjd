#!/usr/bin/env python3


"""
Check colors used in displaying
"""

import argparse
import typing
import os
import sys
import json
import itertools
import colorsys


TRANSPARENCY_OWNER = 0.70


def alpha_compose(background, item):
    """Compose item over background using alpha transparency."""
    return tuple(round(TRANSPARENCY_OWNER * item[i] + (1-TRANSPARENCY_OWNER) * background[i]) for i in range(3))


def rgb_to_hsl(r, g, b):
    """Converts RGB (0-255) to HSL (H en degrees 0-360, S and L in %)"""

    r, g, b = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)  # beware : colorsys returns H,L,S
    return h * 360, s * 100, l * 100


def check_couple_unit_background(name: str, unit, fill, tol_hue=10, gap_min_lum=25) -> None:
    """Checks that the fill has a similar hue and sufficient lightness difference from the unit."""

    h1, s1, l1 = rgb_to_hsl(*unit)
    h2, s2, l2 = rgb_to_hsl(*fill)

    hue_difference = min(abs(h1 - h2), 360 - abs(h1 - h2))  # handles wrap-around 0°/360°
    gap_lum = l2 - l1

    ok_hue = hue_difference <= tol_hue
    ok_lum = gap_lum >= gap_min_lum

    print(f"--- {name} ---")
    print(f"  Unit : H={h1:.1f}° S={s1:.1f}% L={l1:.1f}%")
    print(f"  Filler  : H={h2:.1f}° S={s2:.1f}% L={l2:.1f}%")
    print(f"  Gap hue = {hue_difference:.1f}°  {'OK' if ok_hue else f'⚠️ TOO DIFFERENT because > {tol_hue}'}")
    print(f"  Gap lightness = {gap_lum:.1f} pts  {'OK' if ok_lum else f'⚠️ TOO SMALL should be >= {gap_min_lum}'}")
    print()


def check_pairs_factions(factions, threshold_separation=25) -> None:
    """Compares all factions by unit color to detect potential confusion."""

    print("=== CHECK CONFLICTS BETWEEN FACTIONS (unit color) ===\n")

    conflicts = []
    for n1, n2 in itertools.combinations(factions, 2):
        h1, _, _ = rgb_to_hsl(*factions[n1]["unit"])
        h2, _, _ = rgb_to_hsl(*factions[n2]["unit"])
        gap = min(abs(h1 - h2), 360 - abs(h1 - h2))
        if gap < threshold_separation:
            conflicts.append((n1, n2, gap))

    if not conflicts:
        print("  No conflict detected, all factions are separated enough")
        return

    for n1, n2, gap in sorted(conflicts, key=lambda x: x[2]):
        print(f"  ⚠️  {n1} vs {n2} : gap of {gap:.1f}° (should be >= {threshold_separation}°)")
    print()


def check_colors(background_param: str, json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ check_colors """

    # ----------
    # background
    # ----------
    if len(background_param) != 7:
        print("Incorrect background !")
        sys.exit(1)

    if background_param[0] != '#':
        print("Incorrect background !")
        sys.exit(1)

    try:
        background_tuple = tuple(map(lambda s: int(s, 16), (background_param[1:3], background_param[3:5], background_param[5:7])))
    except ValueError:
        print("Incorrect background !")
        sys.exit(1)

    # ----------
    # parameters
    # ----------

    # load colors
    factions = {}
    for role, role_data in json_parameters_data['roles'].items():
        if int(role) == 0:
            continue

        role_name = role_data['name']
        unit_color_tuple = (role_data['red'][0], role_data['green'][0], role_data['blue'][0])
        unit_color_tuple_rendered = alpha_compose(background_tuple, unit_color_tuple)

        fill_color_tuple = (role_data['red'][1], role_data['green'][1], role_data['blue'][1])
        fill_color_tuple_rendered = alpha_compose(background_tuple, fill_color_tuple)

        factions[role_name] = {"unit": unit_color_tuple_rendered, "fill": fill_color_tuple_rendered}

    # check every pair unit/background individually
    for nom, couleurs in factions.items():
        check_couple_unit_background(nom, couleurs["unit"], couleurs["fill"])

    # check conflicts between factions (hue too close)
    check_pairs_factions(factions, threshold_separation=25)


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-b', '--background', required=True, help='Provide a background color from map file')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file
    background = args.background

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

    check_colors(background, json_parameters_data)


if __name__ == "__main__":
    main()
