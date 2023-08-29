#!/usr/bin/env python3


"""
parses a svg file (from ido) to make json information
variant file is input
parameter file is input and output
"""

import argparse
import typing
import sys
import json
import copy
import struct
import itertools

import xml.dom.minidom

import polylabel

TRACE = False


def get_image_info(file_name: str) -> typing.Tuple[int, int]:
    """ get_image_info """

    with open(file_name, 'rb') as file_ptr:
        data = file_ptr.read()

    assert data.startswith(b'\211PNG\r\n\032\n') and data[12:16] == b'IHDR', "Not a PNG file"
    # PNGs
    width_extracted, height_extracted = struct.unpack(">LL", data[16:24])
    width = int(width_extracted)
    height = int(height_extracted)

    return width, height


class Path:
    """ Path """

    def __init__(self, title_content: str, text: str):
        self._text = text
        self.points: typing.List[typing.Tuple[float, float]] = []
        self._inner_path: typing.Optional['Path'] = None

        #  print(f"{text=}")

        # M : move (do not draw)
        # L : Line
        # V : vertical
        # H : horizontal
        # C : curve : approximative
        # Z : zero (back to first point)

        # first we standardize path
        elements = []
        for elt in self._text.split():
            if len(elt) == 1:
                letter = elt
                elements.append(letter)
            else:
                for letter in ['M', 'L', 'V', 'H', 'C', 'Z']:
                    if elt.startswith(letter):
                        elements.append(letter)
                        elements.append(elt[1:])
                        break
                else:
                    elements.append(elt)

        # then we go through the path
        for elt in elements:

            #  print(f"{elt=}")

            # letters set the automaton state
            if elt in ['M', 'L', 'V', 'H', 'C', 'Z']:
                state = elt
                if state == 'Z':
                    self.points.append(self.points[0])
                continue

            # coordinates get stacked
            # C bezier : approximate
            if state in ['L', 'M', 'C']:
                x_pos, y_pos = map(float, elt.split(','))
            if state == 'H':
                x_pos = float(elt)
            if state == 'V':
                y_pos = float(elt)
            if state == 'Z':
                assert False, f"{title_content} : Z is not at the end"
            if state == 'M':
                assert not self.points, f"{title_content} {text}: M is not at the begining"
            self.points.append((x_pos, y_pos))

    def add_inner(self, path: 'Path') -> None:
        """ add_inner """
        self._inner_path = path

    def middle(self) -> typing.Tuple[float, float]:
        """ middle of area for centers """
        middle_x = (min(p[0] for p in self.points) + max(p[0] for p in self.points)) / 2.
        middle_y = (min(p[1] for p in self.points) + max(p[1] for p in self.points)) / 2.
        return middle_x, middle_y

    def polygon(self) -> typing.List[typing.List[float]]:
        """ polygon """
        return [list(p) for p in self.points]

    def polylabel(self) -> typing.Tuple[float, float]:
        """ middle of area for regions """
        # calculate polylabel

        # list of polygons we pass
        polygons = []

        # the one of the region first
        outer_polygon = self.polygon()
        polygons.append(outer_polygon)

        # some time the one of the inner center
        if self._inner_path:
            inner_polygon = self._inner_path.polygon()
            polygons.append(inner_polygon)

        polylabel_x, polylabel_y = polylabel.polylabel(polygons, precision=0.1)  # type: ignore
        return polylabel_x, polylabel_y

    def __str__(self) -> str:
        return self._text


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_png_input', required=True, help='Input png file (from svg) for getting map size')
    parser.add_argument('-v', '--variant_input', required=True, help='Input variant json file')
    parser.add_argument('-p', '--parameters_input', required=True, help='Input parameters (names) json file')
    parser.add_argument('-s', '--svg_input', required=True, help='Input map svg file')
    parser.add_argument('-F', '--first_format_json_output', required=True, help='Output json file for first format')
    args = parser.parse_args()

    map_png_input = args.map_png_input
    json_variant_input = args.variant_input
    json_parameters_input = args.parameters_input
    svg_input_file = args.svg_input
    first_format_json_output = args.first_format_json_output

    # load variant from json data file
    with open(json_variant_input, "r", encoding='utf-8') as read_file:
        json_variant_data = json.load(read_file)

    # load parameters from json data file
    with open(json_parameters_input, "r", encoding='utf-8') as read_file:
        json_parameters_data = json.load(read_file)

    # make center table from input json file
    centers_name2num_table = {json_parameters_data['zones'][str(n)]['name'].upper(): num + 1 for num, n in enumerate(json_variant_data['centers'])}

    # make region table from input json file
    regions_name2num_table = {v['name'].upper(): int(k) for k, v in json_parameters_data['zones'].items() if v['name']}

    # make table region2center
    region2center_table = {int(k): centers_name2num_table[v['name'].upper()] for k, v in json_parameters_data['zones'].items() if v['name'] and v['name'].upper() in centers_name2num_table}

    # make coastal zone table from input json file
    coastal_zones_name2num_table = {f"{json_parameters_data['zones'][str(r)]['name']}{json_parameters_data['coasts'][str(c)]['name']}".upper(): len(json_variant_data['regions']) + 1 + n for n, (r, c) in enumerate(json_variant_data['coastal_zones'])}

    # parse svg map to find paths
    doc = xml.dom.minidom.parse(svg_input_file)

    # ====== get viewbox =====

    svg_nodes = doc.getElementsByTagName("svg")
    svg_node = svg_nodes[0]
    viewbox = svg_node.getAttribute("viewBox")
    _, _, viewbox_width_str, viewbox_height_str = viewbox.split()
    viewbox_width = float(viewbox_width_str)
    viewbox_height = float(viewbox_height_str)

    # ====== get image dimension =====

    png_width, png_height = get_image_info(map_png_input)
    map_table = {
        'width': int(png_width),
        'height': int(png_height),
    }

    # ====== parse input svg file =====

    centers_path_table: typing.Dict[int, Path] = {}
    regions_path_table: typing.Dict[int, Path] = {}
    coastal_zones_path_table: typing.Dict[int, Path] = {}

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

        # we have a center (octogon)
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
            the_path = Path(title_content, d)
            centers_path_table[number] = the_path

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
            the_path = Path(title_content, d)
            regions_path_table[number] = the_path

        # we have a coastal zone (star)
        if title_content.startswith("ZC_"):

            title_content = title_content.replace("ZC_", "")
            if title_content not in coastal_zones_name2num_table:
                print(f"Cannot give number to coastal zone '{title_content}'")
                sys.exit(1)

            # insert
            number = coastal_zones_name2num_table[title_content]
            if number in coastal_zones_path_table:
                print(f"This coastal zones already has a path '{title_content}'")
                sys.exit(1)
            the_path = Path(title_content, d)
            coastal_zones_path_table[number] = the_path

    doc.unlink()

    # check every center got a path
    for center_name, number in centers_name2num_table.items():
        if number not in centers_path_table:
            print(f"Seems center '{center_name}' did not get a path")
            sys.exit(1)

    # check every region got a path
    for region_name, number in regions_name2num_table.items():
        if number not in regions_path_table:
            print(f"Seems region '{region_name}' did not get a path")
            sys.exit(1)

    # check every coastal zone got a path
    for coastal_zone_name, number in coastal_zones_name2num_table.items():
        if number not in coastal_zones_path_table:
            print(f"Seems coastal zone '{coastal_zone_name}' did not get a path")
            sys.exit(1)

    # make region table from input json file (name of region)
    regions_ref_num_table = {int(k): v['name'] for k, v in json_parameters_data['zones'].items() if v['name']}

    # make display table from input json file (color display of region )
    display_ref_num_table = {int(k): v['display'] for k, v in json_parameters_data['zones'].items() if 'display' in v}

    # put centers path in region paths
    for num, path in regions_path_table.items():
        if num in region2center_table:
            num_center = region2center_table[num]
            path_center = centers_path_table[num_center]
            path.add_inner(path_center)

    # ====== make centers_pos_table =====

    centers_pos_table = {}
    for num, path in sorted(centers_path_table.items(), key=lambda kv: int(kv[0])):

        # for centers : middle is OK
        x_chosen, y_chosen = path.middle()

        centers_pos_table[num] = {
            "x_pos": round(x_chosen * png_width / viewbox_width),
            "y_pos": round(y_chosen * png_height / viewbox_height)
        }

    # ====== make regions_pos_table =====

    regions_pos_table = {}
    regions_area_table = {}
    for num, path in sorted(regions_path_table.items(), key=lambda kv: int(kv[0])):

        # for regions :  the polylabel
        x_chosen, y_chosen = path.polylabel()

        # unit in png coords
        x_unit_pos = round(x_chosen * png_width / viewbox_width)
        y_unit_pos = round(y_chosen * png_height / viewbox_height)

        x_legend_pos = x_unit_pos
        y_legend_pos = y_unit_pos

        # shifts
        y_unit_pos += 7
        y_legend_pos -= 7

        region_name = regions_ref_num_table[num]
        regions_pos_table[num] = {
            "name": region_name,
            "full_name": json_parameters_data['zones'][str(num)]['full_name'],
            "x_pos": x_unit_pos,
            "y_pos": y_unit_pos,
            "x_legend_pos": x_legend_pos,
            "y_legend_pos": y_legend_pos
        }

        if num in display_ref_num_table:
            display = display_ref_num_table[num]
            regions_pos_table[num]["display"] = display

        # little simplification : remove successive duplicates
        raw_list = [(round((x * png_width / viewbox_width)), round((y * png_height / viewbox_height))) for (x, y) in path.polygon()]
        clean_list = [p for p, _ in itertools.groupby(raw_list)]
        if TRACE:
            if clean_list != raw_list:
                print(f"Simplified path of {region_name} from {len(raw_list)} to {len(clean_list)} elements")

        regions_area_table[num] = {
            "area": clean_list
        }

    for num, path in sorted(coastal_zones_path_table.items(), key=lambda kv: int(kv[0])):

        # for special coasts : middle
        x_chosen, y_chosen = path.middle()

        # unit in png coords
        x_unit_pos = round(x_chosen * png_width / viewbox_width)
        y_unit_pos = round(y_chosen * png_height / viewbox_height)

        # legend
        x_legend_pos = x_unit_pos
        y_legend_pos = y_unit_pos

        # shifts
        y_unit_pos += 7
        y_legend_pos -= 7

        regions_pos_table[num] = {
            "name": "",
            "full_name": "",
            "x_pos": x_unit_pos,
            "y_pos": y_unit_pos,
            "x_legend_pos": x_legend_pos,
            "y_legend_pos": y_legend_pos
        }

        # little simplification : remove successive duplicates
        raw_list = [(round((x * png_width / viewbox_width)), round((y * png_height / viewbox_height))) for (x, y) in path.polygon()]
        clean_list = [p for p, _ in itertools.groupby(raw_list)]
        if TRACE:
            if clean_list != raw_list:
                print(f"Simplified path of special coast {num} from {len(raw_list)} to {len(clean_list)} elements")

        regions_area_table[num] = {
            "area": clean_list
        }

    # ============= output ===============

    result1 = copy.deepcopy(json_parameters_data)
    result1['map'] = map_table
    result1['zones'] = regions_pos_table
    result1['centers'] = centers_pos_table
    result1['zone_areas'] = regions_area_table
    output = json.dumps(result1, indent=4, ensure_ascii=False)
    with open(first_format_json_output, 'w', encoding='utf-8') as file_ptr:
        file_ptr.write(output)


if __name__ == '__main__':
    main()
