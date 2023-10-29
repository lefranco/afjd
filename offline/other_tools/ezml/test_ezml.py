#!/usr/bin/env python3


"""
EZML parser

"""

import argparse
import os
import sys
import pathlib

import ezml


# extension of files to scan
EXTENSION_EXPECTED = ".ezml"


class MyEzml(ezml.Ezml):
    """ Specializes ezml class : provides an HTML output for testing purpose """

    def __str__(self) -> str:
        """ HTML output for checking """

        def html_block(block) -> str:

            # HTML
            name = block.name.rstrip('>').lstrip('<')
            if block.attributes:
                name += ' ' + ' '.join([f"{k}={v}" for k, v in block.attributes.items()])
            if block.childs:
                text = f"<{name}>"
                childs_str = ''.join([c if isinstance(c, str) else html_block(c) for c in block.childs])
                text += childs_str
                terminator_str = ezml.Block.terminator(block.name)
                text += terminator_str
            else:
                text = f"<{name} />"
            return text

        return html_block(self.block)


def main() -> None:
    """ main """

    # parameters

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help="EZML file")
    args = parser.parse_args()
    file_path = args.input

    # must exist
    if not os.path.isfile(file_path):
        print("ERROR: Seems file {file_path} does not exist !", file=sys.stderr)
        sys.exit(-1)

    # must have extension
    if pathlib.Path(file_path).suffix != EXTENSION_EXPECTED:
        print(f"ERROR: Seems file {file_path} does not have the extension {EXTENSION_EXPECTED} !", file=sys.stderr)
        sys.exit(-1)

    print(f"Parsing file {file_path}...", file=sys.stderr)
    my_ezml = MyEzml(file_path)

    print(my_ezml)


if __name__ == '__main__':
    main()
