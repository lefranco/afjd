#!/usr/bin/env python3


"""
File : parse.py

parses a svg file to make json information
"""

import argparse
import dataclasses
import typing
import sys
import json
import copy

import xml.dom.minidom  # type: ignore


@dataclasses.dataclass
class Point:
    """ A point """

    letter: str
    x_pos: float
    y_pos: float

    def __init__(self, text: str):
        if text[0].isdigit():
            self.letter = ''
            text = text[0:]
        else:
            self.letter = text[0]
            assert self.letter.isupper()
            text = text[1:]
        text_tab = text.split(',')
        self.x_pos = float(text_tab[0])
        self.y_pos = float(text_tab[1])

    def __str__(self) -> str:
        return f"{self.letter}{self.y_pos},{self.y_pos}"


class Path:
    """ Path """

    def __init__(self, text: str):
        self._text = text
        self.points: typing.List[Point] = list()
        list_x = list()
        list_y = list()

        #  print(f"{text=}")

        for num, elt in enumerate(self._text.split()):
            point = Point(elt)
            #  print(point)
            if num == 0:
                assert point.letter == 'M', f"Hey first letter is {point.letter} not M"
            else:
                assert point.letter in ['', 'L', 'M', 'C'], f"Hey letter is {point.letter} not '', L M or C"
            list_x.append(point.x_pos)
            list_y.append(point.y_pos)

        # calculate middle
        self._middle_x = (min(list_x) + max(list_x)) / 2.
        self._middle_y = (min(list_y) + max(list_y)) / 2.

        # calculate barycenter
        self._barycenter_x = sum(list_x) / len(list_x)
        self._barycenter_y = sum(list_y) / len(list_y)

    def middle(self) -> typing.Tuple[float, float]:
        """ middle of area """
        return self._middle_x, self._middle_y

    def barycenter(self) -> typing.Tuple[float, float]:
        """ middle of area """
        return self._barycenter_x, self._barycenter_y

    def __str__(self) -> str:
        return self._text


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_input', required=True, help='Input variant json file')
    parser.add_argument('-p', '--parameters_input', required=True, help='Input parameters (names) json file')
    parser.add_argument('-s', '--svg_input', required=True, help='Input map svg file')
    parser.add_argument('-F', '--first_format_json_output', required=True, help='Output json file for first format (jeremie)')
    parser.add_argument('-S', '--second_format_json_output', required=True, help='Output json file for second format (wenz)')
    parser.add_argument('-m', '--map_text_output', required=True, help='Output json file for map size')
    args = parser.parse_args()

    json_variant_input = args.variant_input
    json_parameters_input = args.parameters_input
    svg_input_file = args.svg_input
    first_format_json_output = args.first_format_json_output
    second_format_json_output = args.second_format_json_output
    map_text_output = args.map_text_output

    # load variant from json data file
    with open(json_variant_input, "r") as read_file:
        json_variant_data = json.load(read_file)

    # load parameters from json data file
    with open(json_parameters_input, "r") as read_file:
        json_parameters_data = json.load(read_file)

    # make center table from input json file
    centers_name2num_table = {json_parameters_data['zones'][str(n)]['name'].upper(): num + 1 for num, n in enumerate(json_variant_data['centers'])}

    # make region table from input json file
    regions_name2num_table = {v['name'].upper(): int(k) for k, v in json_parameters_data['zones'].items() if v['name']}

    # print(f"{regions_ref_name_table=}", file=sys.stderr)

    # parse svg map to find paths
    doc = xml.dom.minidom.parse(svg_input_file)

    # size

    # ====== make area region json file =====

    svg_nodes = doc.getElementsByTagName("svg")
    svg_node = svg_nodes[0]
    svg_height = svg_node.getAttribute('height')
    svg_width = svg_node.getAttribute('width')
    viewbox = svg_node.getAttribute("viewBox")
    _, _, viewbox_width_str, viewbox_height_str = viewbox.split()
    viewbox_width = float(viewbox_width_str)
    viewbox_height = float(viewbox_height_str)

    # TODO : calculate this
    png_width = 814.
    png_height = 720.

    map_table = {
        'width' : int(png_width),
        'height' : int(png_height),
    }

    centers_path_table: typing.Dict[int, Path] = dict()
    regions_path_table: typing.Dict[int, Path] = dict()

    # ====== parse input svg file =====

    for path in doc.getElementsByTagName("path"):

        path_id = path.getAttribute('id')
        if path_id:
            pass  # print(f"{path_id=}", file=sys.stderr)

        d = path.getAttribute('d')  # pylint: disable=invalid-name
        if not d:
            print("no d")
            continue
        # print(f"{d=}")

        titles = path.getElementsByTagName("title")
        if not titles:
            # print("no title")
            continue
        title = titles[0]
        title_content = title.childNodes[0].nodeValue
        title_content = title_content.upper()
        #  print(f"{title_content=}", file=sys.stderr)

        # we have a center (pos)
        if title_content.startswith("C_"):

            title_content = title_content.replace("C_", "")
            if title_content not in centers_name2num_table:
                print(f"Cannot give number to center '{title_content}'")
                sys.exit(1)

            # insert
            number = centers_name2num_table[title_content]
            if number in centers_path_table:
                print(f"This center already has a path '{title_content}'")
                sys.exit(1)

            # get a point from d
            path = Path(d)
            centers_path_table[number] = path

        # we have a region (area)
        if title_content.startswith("R_"):

            title_content = title_content.replace("R_", "")
            if title_content not in regions_name2num_table:
                print(f"Cannot give number to region '{title_content}'")
                sys.exit(1)

            # insert
            number = regions_name2num_table[title_content]
            if number in regions_path_table:
                print(f"This region already has a path '{title_content}'")
                sys.exit(1)
            path = Path(d)
            regions_path_table[number] = path

    doc.unlink()

    # check every center got a path
    for center, number in centers_name2num_table.items():
        if number not in centers_path_table:
            print(f"Seems center '{center}' did not get a path")
            sys.exit(1)

    # check every region  got a path
    for region, number in regions_name2num_table.items():
        if number not in regions_path_table:
            print(f"Seems region '{region}' did not get a path")
            sys.exit(1)

    # make region table from input json file
    regions_ref_num_table = {int(k): v['name'] for k, v in json_parameters_data['zones'].items() if v['name']}

    # ====== make centers_pos_table =====
    #  for jeremie

    centers_pos_table = dict()
    for num, path in sorted(centers_path_table.items(), key=lambda kv: int(kv[0])):

        x_chosen, y_chosen = path.middle()
#        x_chosen, y_chosen = path.barycenter()

        centers_pos_table[num] = {
            "x_pos": round(x_chosen * png_width / viewbox_width),
            "y_pos": round(y_chosen * png_height / viewbox_height)
        }

    # ====== make regions_pos_table =====
    #  for wenz and jeremie

    regions_pos_table = dict()
    for num, path in sorted(regions_path_table.items(), key=lambda kv: int(kv[0])):

        x_chosen, y_chosen = path.middle()
#        x_chosen, y_chosen = path.barycenter()

        region_name = regions_ref_num_table[num]
        regions_pos_table[num] = {
            "name": region_name,
            "full_name": json_parameters_data['zones'][str(num)]['full_name'],
            "x_legend_pos": round(x_chosen * png_width / viewbox_width),
            "y_legend_pos": round(y_chosen * png_height / viewbox_height),
            "x_pos": round(x_chosen * png_width / viewbox_width),
            "y_pos": round(y_chosen * png_height / viewbox_height)
        }

    # ====== make map_elements =====
    #  for wenz

    map_elements: typing.List[typing.List[typing.Any]] = list()

    for num, path in sorted(regions_path_table.items(), key=lambda kv: int(kv[0])):

        map_element: typing.List[typing.Any] = list()

        # put 'path' (always)
        map_element.append(["path"])

        # build infos
        infos = list()

        infos.append("a")
        region_type_code = json_variant_data['regions'][num - 1]
        assert region_type_code in [1, 2, 3]
        infos.append("l" if region_type_code in [1, 2] else "w")
        region_name = regions_ref_num_table[num]
        infos.append(region_name)
        infos.append(str(num))

        # put infos
        map_element.append(infos)

        # put path
        map_element.append([str(path)])

        # put in map elements
        map_elements.append(map_element)

    # ============= output ===============

    result1 = copy.deepcopy(json_parameters_data)
    result1['map'] = map_table
    result1['zones'] = regions_pos_table
    result1['centers'] = centers_pos_table
    output = json.dumps(result1, indent=4)
    with open(first_format_json_output, 'w') as file_ptr:
        file_ptr.write(output)

    result2 = dict()
    result2['map_elements'] = map_elements
    output = json.dumps(result2, indent=4)
    with open(second_format_json_output, 'w') as file_ptr:
        file_ptr.write(output)

    with open(map_text_output, 'w') as file_ptr:
        file_ptr.write(f"map size is :\n")
        file_ptr.write(f"{svg_width=} {svg_height}\n")
        file_ptr.write(f"{png_width=} {png_height=}\n")


if __name__ == '__main__':
    main()
