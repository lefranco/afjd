#!/usr/bin/env python3

"""
Graphic tool to adjust positions centers
"""

# pylint: disable=multiple-statements

import argparse
import typing
import os
import configparser
import sys
import json
import math

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext


# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

TITLE = "Adjust centers : \nclick to select center, arrows to move selected, + to move faster, - to move slower,\n u to undo last action and save button to save to file"


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

FONT = ('Arial 7')

SHIFT_LEGEND_X = 0
SHIFT_LEGEND_Y = -4
DELTA_LEGEND_EXPECTED_X = 0
DELTA_LEGEND_EXPECTED_Y = -14


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name


def stabbeur_center(x: int, y: int, canvas: typing.Any, outline: str, fill: str) -> None:  # pylint: disable=invalid-name
    """ display a center the stabbeur way """

    item = canvas.create_oval(x - 5, y - 5, x + 5, y + 5, outline=outline, fill=fill)
    return item


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, variant_file: str, parameters_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # load variant data from json data file
        with open(variant_file, "r", encoding='utf-8') as read_file:
            try:
                self.json_variant_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {variant_file} : {exception}")
                sys.exit(-1)

        # load parameters from json data file
        with open(parameters_file, "r", encoding='utf-8') as read_file:
            try:
                self.json_parameters_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {parameters_file} : {exception}")
                sys.exit(-1)

        # data
        self.focused_num_center: typing.Optional[int] = None

        # centers
        self.centers_data = self.json_parameters_data['centers']

        # speed
        self.speed = 1

        # items table
        self.item_table: typing.Dict[int, typing.Any] = {}

        # backup
        self.prev_center_data: typing.Dict[str, int] = {}

        # actual creation of widgets
        self.create_widgets(self, map_file, parameters_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str, parameters_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def erase(num_center: int) -> None:

            item = self.item_table[num_center]
            self.canvas.delete(item)

        def draw(num_center: int, highlited: bool) -> None:

            center_data = self.centers_data[str(num_center)]
            x_pos_read = center_data['x_pos']
            y_pos_read = center_data['y_pos']

            outline = 'red' if highlited else 'blue'
            fill = 'grey'
            item = stabbeur_center(x_pos_read, y_pos_read, self.canvas, outline, fill)
            self.item_table[num_center] = item

        def arrow_callback(event: typing.Any) -> None:

            if self.focused_num_center is None:
                return

            # erase
            erase(self.focused_num_center)

            center_data = self.centers_data[str(self.focused_num_center)]
            self.prev_center_data = center_data.copy()

            if event.keysym == 'Right':
                center_data['x_pos'] += self.speed
            if event.keysym == 'Left':
                center_data['x_pos'] -= self.speed
            if event.keysym == 'Down':
                center_data['y_pos'] += self.speed
            if event.keysym == 'Up':
                center_data['y_pos'] -= self.speed

            # draw
            draw(self.focused_num_center, True)

        def click_callback(event: typing.Any) -> None:
            x_mouse, y_mouse = event.x, event.y

            # update on screen
            if self.focused_num_center is not None:
                erase(self.focused_num_center)
                draw(self.focused_num_center, False)

            min_dist = 100000.
            self.focused_num_center = None

            for num_center_str, center_data in self.centers_data.items():

                center_x, center_y = center_data['x_pos'] + SHIFT_LEGEND_X, center_data['y_pos'] + SHIFT_LEGEND_Y
                dist = math.sqrt((center_x - x_mouse) ** 2 + (center_y - y_mouse) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    self.focused_num_center = int(num_center_str)

            assert self.focused_num_center is not None

            # update on screen
            erase(self.focused_num_center)
            draw(self.focused_num_center, True)
            region_num = self.json_variant_data['centers'][self.focused_num_center-1]
            region_name = self.json_parameters_data['zones'][str(region_num)]['name']
            region_full_name = self.json_parameters_data['zones'][str(region_num)]['full_name']
            self.center_selected.config(text = f"{region_full_name} ({region_name})")

        def key_callback(event: typing.Any) -> None:
            if event.char == '+':
                self.speed += 1
            if event.char == '-':
                if self.speed > 1:
                    self.speed -= 1

        def undo_callback(_: typing.Any) -> None:

            if self.focused_num_center is None:
                return

            erase(self.focused_num_center)

            center_data = self.prev_center_data.copy()
            self.centers_data[str(self.focused_num_center)] = center_data

            # update on screen
            draw(self.focused_num_center, True)

        def save_callback() -> None:

            output = json.dumps(self.json_parameters_data, indent=4, ensure_ascii=False)
            with open(parameters_file, "w", encoding='utf-8') as write_file:
                write_file.write(output)

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

        frame_carto = tkinter.Frame(main_frame)
        frame_carto.grid(row=2, column=1, sticky='we')

        self.map_file = map_file
        self.filename = tkinter.PhotoImage(file=self.map_file)

        self.canvas = tkinter.Canvas(frame_carto, width=self.filename.width(), height=self.filename.height())
        self.canvas.grid(row=1, column=1)

        # map
        self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.filename)

        # centers
        for num_center_str in self.centers_data:
            num_center = int(num_center_str)
            draw(num_center, False)

        # clicking
        self.canvas.bind("<Button-1>", click_callback)

        # arrows
        self.master.bind("<Left>", arrow_callback)
        self.master.bind("<Right>", arrow_callback)
        self.master.bind("<Up>", arrow_callback)
        self.master.bind("<Down>", arrow_callback)

        # ctrl
        self.master.bind("<Key>", key_callback)
        self.master.bind("<Key-u>", undo_callback)

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.Frame(main_frame)
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.center_selected = tkinter.Label(frame_buttons_information, text="-", justify=tkinter.LEFT)
        self.center_selected.grid(row=2, column=1, sticky='we')

        self.save_button = tkinter.Button(frame_buttons_information, text="save", command=save_callback)
        self.save_button.grid(row=3, column=1, sticky='we')

    def menu_complete_quit(self) -> None:

        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def main_loop(map_file: str, variant_file: str, parameters_file: str) -> None:
    """ main_loop """

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with map file '{map_file}' and parameter file '{parameters_file}'...")

    # use description of first register as overall title
    window_name = "Diplomania map center position adjustment tool"

    # create app
    root.title(window_name)

    app = Application(map_file, variant_file, parameters_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_file', required=True, help='Load a map file at start')
    parser.add_argument('-v', '--variant_file', required=True, help='Load variant json file')
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file
    variant_file = args.variant_file
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

    main_loop(map_file, variant_file, parameters_file)

    print("The End")


if __name__ == "__main__":
    main()
