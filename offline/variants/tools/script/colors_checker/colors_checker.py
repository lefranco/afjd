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


def rgb_to_hsl(r, g, b):
    """Convertit RGB (0-255) en HSL (H en degrés 0-360, S et L en %)"""

    r, g, b = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)  # attention : colorsys renvoie H,L,S
    return h * 360, s * 100, l * 100


def check_couple_unit_background(nom, unite, fond, tol_teinte=10, ecart_min_lum=25):
    """Vérifie qu'une paire (unité, fond) est bien une même teinte éclaircie"""

    h1, s1, l1 = rgb_to_hsl(*unite)
    h2, s2, l2 = rgb_to_hsl(*fond)

    ecart_teinte = min(abs(h1 - h2), 360 - abs(h1 - h2))  # gère le wrap-around 0°/360°
    ecart_lum = l2 - l1

    ok_teinte = ecart_teinte <= tol_teinte
    ok_lum = ecart_lum >= ecart_min_lum

    print(f"--- {nom} ---")
    print(f"  Unit : H={h1:.1f}° S={s1:.1f}% L={l1:.1f}%")
    print(f"  Background  : H={h2:.1f}° S={s2:.1f}% L={l2:.1f}%")
    print(f"  Gap hue = {ecart_teinte:.1f}°  {'OK' if ok_teinte else '⚠️ TOO DIFFERENT'}")
    print(f"  Gap luminosity = {ecart_lum:.1f} pts  {'OK' if ok_lum else '⚠️ TOO SMALL'}")
    print()
    return ok_teinte and ok_lum


def check_pairs_factions(factions, seuil_separation=25):
    """Compare toutes les factions entre elles (sur leur couleur d'unité) pour repérer les confusions"""
    
    print("=== CHECK CONFLICTS BETWEEN FACTIONS (unit color) ===\n")

    conflits = []
    for n1, n2 in itertools.combinations(factions, 2):
        h1, _, _ = rgb_to_hsl(*factions[n1]["unite"])
        h2, _, _ = rgb_to_hsl(*factions[n2]["unite"])
        ecart = min(abs(h1 - h2), 360 - abs(h1 - h2))
        if ecart < seuil_separation:
            conflits.append((n1, n2, ecart))

    if conflits:
        for n1, n2, ecart in sorted(conflits, key=lambda x: x[2]):
            print(f"  ⚠️  {n1} vs {n2} : gap of {ecart:.1f}° (threshold = {seuil_separation}°)")
    else:
        print("  No conflict detected, all factions are separated enough")
    print()


def check_colors(json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ check_colors """

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
        background_color_tuple = (role_data['red'][1], role_data['green'][1], role_data['blue'][1])

        factions[role_name] = {"unite": unit_color_tuple, "fond": background_color_tuple}

    # 1. Check every pair unit/background individually
    for nom, couleurs in factions.items():
        check_couple_unit_background(nom, couleurs["unite"], couleurs["fond"])

    # 2. Check conflicts between factions (hue too close)
    check_pairs_factions(factions, seuil_separation=25)


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

    check_colors(json_parameters_data)


if __name__ == "__main__":
    main()
