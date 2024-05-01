#!/usr/bin/env python3


"""
Extracts positions, polygons, polygon middle from map
Uses opencv version is 4.6.0
"""

import argparse
import typing
import os
import configparser
import sys
import itertools
import json

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

import cv2  # type: ignore

import geometry
import polylabel

# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

INFO_HEIGHT1 = 3
INFO_WIDTH1 = 30

INFO_HEIGHT2 = 15
INFO_WIDTH2 = 30

BUTTONS_PER_COLUMN = 24

TITLE = "Polygons positions detection : click anywhere to get information to be copied pasted"


class VersionRecord(typing.NamedTuple):
    """ All version related information  """

    name: str
    date: str
    hour: str

    major: int
    minor: int
    revision: int

    comment: str

    def short(self) -> str:
        """ short version of version """
        return f"Version {self.major}.{self.minor} rev {self.revision} ({self.name})"

    def __str__(self) -> str:
        return f"{self.name} version {self.major}.{self.minor} rev {self.revision}\nDated {self.date} {self.hour}\n\nComment : {self.comment}"


def load_version_information() -> VersionRecord:
    """ For testing """

    # Where is the file ?
    version_file = VERSION_FILE_NAME
    assert os.path.isfile(version_file), f"Please create file {version_file}"

    config = configparser.ConfigParser()
    config.read(version_file)

    section = VERSION_SECTION

    paragraph_name = section.upper()
    data = config[paragraph_name]

    name = data['name']
    date = data['date']
    hour = data['hour']

    major = int(data['major'])
    minor = int(data['minor'])
    revision = int(data['revision'])

    comment = data['comment']

    version_information = VersionRecord(name=name, date=date, hour=hour, major=major, minor=minor, revision=revision, comment=comment)
    return version_information


VERSION_INFORMATION = load_version_information()


class MyText(tkinter.Text):
    """ MyText """

    def __init__(self, root: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> None:
        tkinter.Text.__init__(self, *args, **kwargs)
        self.config(state=tkinter.DISABLED)
        self._root = root
        self._content = ""

    def display(self, content: str) -> None:
        """ display """

        self._content = content

        self.config(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, content)
        #  self.see("end")
        self.config(state=tkinter.DISABLED)

    def clipboard(self) -> None:
        """ clipboard """

        self._root.clipboard_clear()
        self._root.clipboard_append(self._content)

DELTA_LEGEND_EXPECTED_X = 0
DELTA_LEGEND_EXPECTED_Y = -14

class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, variant_file: str, parameters_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # data to export
        self.export_data: typing.Dict[str, typing.Any] = {}

        # actual creation of widgets
        self.create_widgets(self, map_file, variant_file, parameters_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str, variant_file: str, parameters_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def put_image() -> None:

            self.image_map = tkinter.PhotoImage(file=self.map_file)  # pylint: disable=attribute-defined-outside-init

            self.canvas = tkinter.Canvas(frame_carto, width=self.image_map.width(), height=self.image_map.height())  # pylint: disable=attribute-defined-outside-init
            self.canvas.grid(row=1, column=1)

            # canvas
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.image_map)

            # clicking
            self.canvas.bind("<Button-1>", click_callback)

        def click_callback(event: typing.Any) -> None:

            x_mouse, y_mouse = event.x, event.y

            information1 = f'"x_pos": {x_mouse},\n"y_pos": {y_mouse}'
            self.mouse_pos.display(information1)

            information2 = ""

            # erase
            self.polygon.display(information2)

            put_image()

            # data to export
            self.export_data = {}

            for x_pos, y_pos, w_val, h_val in CONTOUR_TABLE:

                # must be inside box
                if not x_pos <= x_mouse <= x_pos + w_val and y_pos <= y_mouse <= y_pos + h_val:
                    continue

                # get poly created
                poly = CONTOUR_TABLE[(x_pos, y_pos, w_val, h_val)]

                # must be inside poly
                designated_pos = geometry.PositionRecord(x_pos=x_mouse, y_pos=y_mouse)
                area_poly = geometry.Polygon([geometry.PositionRecord(*t) for t in poly])  # type: ignore
                if not area_poly.is_inside_me(designated_pos):
                    continue

                # display on map
                flat_points = itertools.chain.from_iterable(poly)  # type: ignore
                self.canvas.create_polygon(*flat_points, fill='red', outline='blue', stipple='gray25')

                # display as text
                information2 = str(poly)
                self.polygon.display(information2)

                # store as data

                # middle
                polygons = [poly]
                polylabel_x_f, polylabel_y_f = polylabel.polylabel(polygons, precision=0.1)  # type: ignore
                polylabel_x, polylabel_y = round(polylabel_x_f), round(polylabel_y_f)
                self.canvas.create_line(polylabel_x + 5, polylabel_y, polylabel_x - 5, polylabel_y, fill='blue')
                self.canvas.create_line(polylabel_x, polylabel_y + 5, polylabel_x, polylabel_y - 5, fill='blue')
                information2 = f'"x_pos": {polylabel_x},\n"y_pos": {polylabel_y}'
                self.middle_pos.display(information2)

                # store as data
                self.export_data['poly'] = poly
                self.export_data['x_middle_pos'] = polylabel_x
                self.export_data['y_middle_pos'] = polylabel_y
                self.export_data['x_click_pos'] = x_mouse
                self.export_data['y_click_pos'] = y_mouse

                # only first
                break

            else:
                information2 = "Failed!"
                self.polygon.display(information2)

        def export_zone_callback(num: int) -> None:

            if not self.export_data:
                tkinter.messagebox.showinfo(title="Error", message="Nothing to export !")
                return

            # load parameters from json data file
            with open(self.parameters_file, "r", encoding='utf-8') as read_file:
                try:
                    json_parameters_data = json.load(read_file)
                except Exception as exception:  # pylint: disable=broad-except
                    print(f"Failed to load {parameters_file} : {exception}")
                    sys.exit(-1)

            # update pos
            if str(num) not in json_parameters_data['zones']:
                json_parameters_data['zones'][str(num)] = {}
            json_parameters_data['zones'][str(num)]['x_pos'] = self.export_data['x_middle_pos']
            json_parameters_data['zones'][str(num)]['y_pos'] = self.export_data['y_middle_pos']
            json_parameters_data['zones'][str(num)]['x_legend_pos'] = self.export_data['x_middle_pos'] + DELTA_LEGEND_EXPECTED_X
            json_parameters_data['zones'][str(num)]['y_legend_pos'] = self.export_data['y_middle_pos'] + DELTA_LEGEND_EXPECTED_Y

            # update poly
            if 'zone_areas' not in json_parameters_data:
                json_parameters_data['zone_areas'] = {}
            if str(num) not in json_parameters_data['zone_areas']:
                json_parameters_data['zone_areas'][str(num)] = {}
            json_parameters_data['zone_areas'][str(num)]['area'] = self.export_data['poly']

            # save parameters to json data file
            output = json.dumps(json_parameters_data, indent=4, ensure_ascii=False)
            with open(self.parameters_file, 'w', encoding='utf-8') as file_ptr:
                file_ptr.write(output)

            # update button
            button = self._export_zone_button_table[num]
            button['relief'] = tkinter.SUNKEN

        def export_center_callback(num: int) -> None:

            if not self.export_data:
                tkinter.messagebox.showinfo(title="Error", message="Nothing to export !")
                return

            # load parameters from json data file
            with open(self.parameters_file, "r", encoding='utf-8') as read_file:
                try:
                    json_parameters_data = json.load(read_file)
                except Exception as exception:  # pylint: disable=broad-except
                    print(f"Failed to load {parameters_file} : {exception}")
                    sys.exit(-1)

            # update center
            if 'centers' not in json_parameters_data:
                json_parameters_data['centers'] = {}
            if str(num) not in json_parameters_data['centers']:
                json_parameters_data['centers'][str(num)] = {}
            json_parameters_data['centers'][str(num)]['x_pos'] = self.export_data['x_click_pos']
            json_parameters_data['centers'][str(num)]['y_pos'] = self.export_data['y_click_pos']

            # save parameters to json data file
            output = json.dumps(json_parameters_data, indent=4, ensure_ascii=False)
            with open(self.parameters_file, 'w', encoding='utf-8') as file_ptr:
                file_ptr.write(output)

            # update button
            button = self._export_center_button_table[num]
            button['relief'] = tkinter.SUNKEN

        def reload_callback() -> None:

            # redo study
            study_image(self.map_file, False)

            put_image()

        def copy_position_callback() -> None:
            self.mouse_pos.clipboard()

        def copy_area_callback() -> None:
            self.polygon.clipboard()

        def copy_position2_callback() -> None:
            self.middle_pos.clipboard()

        self.menu_bar = tkinter.Menu(main_frame)

        self.menu_file = tkinter.Menu(self.menu_bar, tearoff=0)
        self.menu_file.add_command(label="Exit", command=self.menu_complete_quit)
        self.menu_bar.add_cascade(label="File", menu=self.menu_file)

        self.menu_help = tkinter.Menu(self.menu_bar, tearoff=0)
        self.menu_help.add_command(label="About...", command=about)
        self.menu_bar.add_cascade(label="Help", menu=self.menu_help)

        self.master.config(menu=self.menu_bar)  # type: ignore

        # frame title
        # -----------

        frame_title = tkinter.Frame(main_frame)
        frame_title.grid(row=1, column=1, sticky='we')

        label = tkinter.Label(frame_title, text=TITLE, justify=tkinter.LEFT)
        label.grid(row=1, column=1, sticky='we')

        # frame carto
        # -----------

        frame_carto = tkinter.LabelFrame(main_frame, text="The map")
        frame_carto.grid(row=2, column=1, sticky='we')

        self.map_file = map_file
        put_image()

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.LabelFrame(main_frame, text="Selection and information")
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.reload_button = tkinter.Button(frame_buttons_information, text="Reload map file", command=reload_callback)
        self.reload_button.grid(row=0, column=1, sticky='we')

        self.mouse_pos_label = tkinter.Label(frame_buttons_information, text="Position of click :")
        self.mouse_pos_label.grid(row=1, column=1, sticky='we')

        self.mouse_pos = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT1, width=INFO_WIDTH1)
        self.mouse_pos.grid(row=2, column=1, sticky='we')

        self.mouse_pos_button = tkinter.Button(frame_buttons_information, text="copy click position", command=copy_position_callback)
        self.mouse_pos_button.grid(row=3, column=1, sticky='we')

        self.polygon_label = tkinter.Label(frame_buttons_information, text="Polygon around click :")
        self.polygon_label.grid(row=4, column=1, sticky='we')

        self.polygon = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT2, width=INFO_WIDTH2)
        self.polygon.grid(row=5, column=1, sticky='we')

        self.polygon_button = tkinter.Button(frame_buttons_information, text="copy area", command=copy_area_callback)
        self.polygon_button.grid(row=6, column=1, sticky='we')

        self.middle_pos_label = tkinter.Label(frame_buttons_information, text="Position of middle of polygon :")
        self.middle_pos_label.grid(row=7, column=1, sticky='we')

        self.middle_pos = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT1, width=INFO_WIDTH1)
        self.middle_pos.grid(row=8, column=1, sticky='we')

        self.middle_pos_button = tkinter.Button(frame_buttons_information, text="copy middle position", command=copy_position2_callback)
        self.middle_pos_button.grid(row=9, column=1, sticky='we')

        # frame export
        # -----------
        self.export_data = {}
        self.variant_file = variant_file
        self.parameters_file = parameters_file

        # load variant data from json data file
        with open(self.variant_file, "r", encoding='utf-8') as read_file:
            try:
                json_variant_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {variant_file} : {exception}")
                sys.exit(-1)

        # load parameters from json data file
        with open(self.parameters_file, "r", encoding='utf-8') as read_file:
            try:
                json_parameters_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {parameters_file} : {exception}")
                sys.exit(-1)

        frame_export_zones = tkinter.LabelFrame(main_frame, text="Export zones (polygon + middle)")
        frame_export_zones.grid(row=2, column=3, sticky='nw')

        self._export_zone_button_table = {}

        export_buttons_table = {}
        for number, zone in json_parameters_data['zones'].items():

            if zone['name']:
                legend = zone['name']
            else:
                zone_num = int(number) - len(json_variant_data['regions'])
                region_num, coast_num = json_variant_data['coastal_zones'][zone_num - 1]
                region_name = json_parameters_data['zones'][str(region_num)]['name']
                coast_name = json_parameters_data['coasts'][str(coast_num)]['name']
                legend = f"{region_name}{coast_name}"

            export_button = tkinter.Button(frame_export_zones, text=legend, command=lambda number=number: export_zone_callback(int(number)))  # type: ignore
            if 'zone_areas' in json_parameters_data and number in json_parameters_data['zone_areas']:
                export_button['relief'] = tkinter.SUNKEN
            self._export_zone_button_table[int(number)] = export_button

            export_buttons_table[legend] = export_button

        # display sorted (easier)
        for num, (_, export_button) in enumerate(sorted(export_buttons_table.items(), key = lambda t: t[0].upper())):
            export_button.grid(row=num % BUTTONS_PER_COLUMN + 1, column=num // BUTTONS_PER_COLUMN + 1, sticky='we')

        frame_export_centers = tkinter.LabelFrame(main_frame, text="Export centers (click)")
        frame_export_centers.grid(row=2, column=4, sticky='nw')

        self._export_center_button_table = {}

        export_buttons_table = {}
        for number in map(str, range(1, 1 + len(json_variant_data['centers']))):

            num_zone = json_variant_data['centers'][int(number) - 1]
            legend = json_parameters_data['zones'][str(num_zone)]['name']
            export_button = tkinter.Button(frame_export_centers, text=legend, command=lambda number=number: export_center_callback(int(number)))  # type: ignore
            if 'centers' in json_parameters_data and number in json_parameters_data['centers']:
                export_button['relief'] = tkinter.SUNKEN
            self._export_center_button_table[int(number)] = export_button
            export_buttons_table[legend] = export_button

        # display sorted (easier)
        for num, (_, export_button) in enumerate(sorted(export_buttons_table.items(), key = lambda t: t[0])):
            export_button.grid(row=num % BUTTONS_PER_COLUMN + 1, column=num // BUTTONS_PER_COLUMN + 1, sticky='we')

    def menu_complete_quit(self) -> None:
        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def study_image(map_file: str, debug: bool) -> None:
    """ study_image """

    global CONTOUR_TABLE

    CONTOUR_TABLE = {}

    image = cv2.imread(map_file)  # pylint: disable=c-extension-no-member

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # pylint: disable=c-extension-no-member

    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # pylint: disable=c-extension-no-member

    # Filter using contour h
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # pylint: disable=c-extension-no-member

    for current_contour in contours:

        x_pos, y_pos, w_val, h_val = cv2.boundingRect(current_contour)  # pylint: disable=c-extension-no-member

        current_contour2 = cv2.approxPolyDP(current_contour, 1, True)  # pylint: disable=c-extension-no-member

        CONTOUR_TABLE[(x_pos, y_pos, w_val, h_val)] = list(map(lambda p: p[0], current_contour2.tolist()))  # type: ignore

    # sort to put smaller first bounding rect first
    CONTOUR_TABLE = {k: CONTOUR_TABLE[k] for k in sorted(CONTOUR_TABLE, key=lambda b: b[2] * b[3])}

    if debug:
        cv2.imshow('image', thresh)  # pylint: disable=c-extension-no-member
        cv2.waitKey()  # pylint: disable=c-extension-no-member
        sys.exit()


CONTOUR_TABLE: typing.Dict[typing.Tuple[int, int, int, int], typing.List[int]] = {}


def main_loop(debug: bool, map_file: str, variant_file: str, parameters_file: str) -> None:
    """ main_loop """

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with map file '{map_file}'...")

    # use description of first register as overall title
    window_name = "Diplomania map zone extracting tool"

    # create app
    root.title(window_name)

    app = Application(map_file, variant_file, parameters_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # for polygons : use opencv
    study_image(map_file, debug)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='Show contours (debug)', action='store_true')
    parser.add_argument('-m', '--map_file', required=True, help='Load a map file at start')
    parser.add_argument('-v', '--variant_file', required=True, help='Load variant json file')
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    debug = args.debug
    variant_file = args.variant_file
    map_file = args.map_file
    parameters_file = args.parameters_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(variant_file):
        print(f"File '{variant_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(parameters_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    main_loop(debug, map_file, variant_file, parameters_file)

    print("The End")


if __name__ == "__main__":
    main()
