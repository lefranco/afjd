#!/usr/bin/env python3


"""
File : optimize.py

optimize parameter file
"""

import argparse
import json


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_input', required=True, help='Input parameters json file')
    parser.add_argument('-F', '--first_format_json_output', required=True, help='Output optimized parameters json file')
    args = parser.parse_args()

    json_parameters_input = args.parameters_input
    first_format_json_output = args.first_format_json_output

    # load parameters from json data file
    with open(json_parameters_input, "r", encoding='utf-8') as read_file:
        json_parameters_data = json.load(read_file)

    # ============= optim ===============

    result = json_parameters_data

    # ============= output ===============

    output = json.dumps(result, indent=4, ensure_ascii=False)
    with open(first_format_json_output, 'w', encoding='utf-8') as file_ptr:
        file_ptr.write(output)


if __name__ == '__main__':
    main()
