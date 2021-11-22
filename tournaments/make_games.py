#!/usr/bin/env python3

""" This is a rework of famous generatefromFID software
This module implements the upper layer
"""

import typing
import argparse
import os.path

# pypi
import openpyxl  # type: ignore


GAMES_SHEET = 'Parties_1er tour'

roles = ['name', 'master', 'eng', 'fra', 'ger', 'ita', 'aus', 'rus', 'tur']


def parse_games(input_file_name: str) -> None:
    """ Parse the games """

    workbook = openpyxl.load_workbook(input_file_name)

    spreadsheet = workbook.active

    for num_row, row_content in enumerate(spreadsheet):

        game = dict()

        for num_col, col in enumerate(row_content):

            role = roles[num_col]
            pseudo = col.value.replace(' ','_')
            game[role] = pseudo

        print(game)


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tournament', required=True, help='Tournament description file')
    args = parser.parse_args()

    input_file_name = args.tournament
    if not os.path.exists(input_file_name):
        print(f"ERROR : No such file as '{input_file_name}'.")
        exit(1)
    print(f"Using  file {input_file_name} as input...")

    # Parse registers
    parse_games(input_file_name)


if __name__ == "__main__":
    main()
