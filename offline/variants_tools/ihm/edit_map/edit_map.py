#!/usr/bin/env python3


"""
Edit map to have only sea, land (including coasts) and unpassable areas.
Uses opencv version is 4.6.0
"""

import argparse
import typing
import os
import configparser
import sys
import enum
import tempfile
import json
import math

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

import numpy as np

import cv2  # type: ignore


# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

INFO_HEIGHT = 1
INFO_WIDTH = 10

BUTTONS_PER_COLUMN = 24

TITLE = "Map editor, select fill type and click on map to fill"

# File with colors
COLORS_FILE_NAME = "./colors.ini"


# Paint brush
MAX_THICKNESS = 20
START_THICKNESS = 10

# Special coast
COAST_MARKER_RADIUS = 7
COAST_MARKER_COLOR = (0, 0, 0)  # Black
COAST_MARKER_THICKNESS = 1
COAST_MARKER_DIVISIONS = 6

CENTER_RADIUS = 5

@enum.unique
class FillType(enum.Enum):
    """ FillType """

    LAND_COAST = enum.auto()
    SEA = enum.auto()
    UNPASSABLE = enum.auto()


@enum.unique
class FillMode(enum.Enum):
    """ FillMode """

    FILL = enum.auto()
    PAINT = enum.auto()
    SPECIAL_COAST = enum.auto()


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


def load_colors() -> typing.Dict[FillType, typing.Dict[str, int]]:
    """ load_colors """

    # Where is the file ?
    colors_file = COLORS_FILE_NAME
    assert os.path.isfile(colors_file), f"Please create file {colors_file}"

    config = configparser.ConfigParser()
    config.read(colors_file)

    colors_dict = {}
    for fill_type in FillType:
        colors_dict[fill_type] = {k: int(v) for k, v in dict(config[fill_type.name]).items()}

    return colors_dict


COLORS_TABLE = load_colors()


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


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, parameters_file: typing.Optional[str], master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # map file
        self.parameters_file = parameters_file

        # map file
        self.map_file = map_file

        # image for tkinter
        self.image_map = tkinter.PhotoImage(file=map_file)

        # image for cv
        self.cv_image = cv2.imread(map_file)  # pylint: disable=c-extension-no-member

        # stack of images
        self.images_stack: typing.List[typing.Any] = []

        # current fill type
        self.fill_type_selected: typing.Optional[FillType] = None
        self.fill_mode_selected: typing.Optional[FillMode] = None
        self.thickness_selected = START_THICKNESS

        # actual creation of widgets
        self.create_widgets(self, map_file)

        information = f"{self.thickness_selected} px"
        self.thickness_value.display(information)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def hexagon(x_pos: int, y_pos: int, color_tuple: typing.Tuple[int,...]) -> None:

            # calculate points
            subangle = 2 * math.pi / COAST_MARKER_DIVISIONS
            points = np.array([[x_pos + COAST_MARKER_RADIUS * math.cos(subangle * i_val),
                                y_pos + COAST_MARKER_RADIUS * math.sin(subangle * i_val)]
                               for i_val in range(COAST_MARKER_DIVISIONS)], np.int32)

            # draw
            cv2.polylines(self.cv_image, [points], True, color_tuple, COAST_MARKER_THICKNESS)  # pylint: disable=c-extension-no-member

        def circle(x_pos: int, y_pos: int, color_tuple: typing.Tuple[int,...]) -> None:

            # draw
            cv2.circle(self.cv_image, (x_pos, y_pos), CENTER_RADIUS, color_tuple, COAST_MARKER_THICKNESS)  # pylint: disable=c-extension-no-member

        def put_image() -> None:

            self.canvas = tkinter.Canvas(frame_carto, width=self.image_map.width(), height=self.image_map.height())  # pylint: disable=attribute-defined-outside-init
            self.canvas.grid(row=1, column=1)

            # canvas
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.image_map)

            # clicking
            self.canvas.bind("<Button-1>", click_callback)

        def coasts_zones_callback(erase: bool) -> None:

            if self.parameters_file is None:
                tkinter.messagebox.showinfo(title="Error", message=("Please pass parameters file json as parameter of program!"))
                return

            if not os.path.exists(self.parameters_file):
                tkinter.messagebox.showinfo(title="Error", message=(f"File '{self.parameters_file}' does not seem to exist, please advise !"))
                return

            # load parameters from json data file
            with open(self.parameters_file, "r", encoding='utf-8') as read_file:
                try:
                    json_parameters_data = json.load(read_file)
                except Exception as exception:  # pylint: disable=broad-except
                    tkinter.messagebox.showinfo(title="Error", message=(f"Failed to load {self.parameters_file} : {exception}"))
                    return

            if erase:
                color = COLORS_TABLE[FillType.LAND_COAST]
                color_tuple = tuple(reversed(color.values()))
            else:
                color_tuple = COAST_MARKER_COLOR

            for zone_data in json_parameters_data['zones'].values():

                if zone_data['name']:
                    continue

                x_center = zone_data['x_pos']
                y_center = zone_data['y_pos']

                hexagon(x_center, y_center, color_tuple)

            # Pass image cv -> tkinter
            _, tmp_file = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmp_file, self.cv_image)  # pylint: disable=c-extension-no-member
            self.image_map = tkinter.PhotoImage(file=tmp_file)
            os.remove(tmp_file)

            # Display on screen
            put_image()

        def centers_callback(erase: bool) -> None:

            if self.parameters_file is None:
                tkinter.messagebox.showinfo(title="Error", message=("Please pass parameters file json as parameter of program!"))
                return

            if not os.path.exists(self.parameters_file):
                tkinter.messagebox.showinfo(title="Error", message=(f"File '{self.parameters_file}' does not seem to exist, please advise !"))
                return

            # load parameters from json data file
            with open(self.parameters_file, "r", encoding='utf-8') as read_file:
                try:
                    json_parameters_data = json.load(read_file)
                except Exception as exception:  # pylint: disable=broad-except
                    tkinter.messagebox.showinfo(title="Error", message=(f"Failed to load {self.parameters_file} : {exception}"))
                    return

            if erase:
                color = COLORS_TABLE[FillType.LAND_COAST]
                color_tuple = tuple(reversed(color.values()))
            else:
                color_tuple = COAST_MARKER_COLOR

            for center_data in json_parameters_data['centers'].values():

                x_center = center_data['x_pos']
                y_center = center_data['y_pos']

                circle(x_center, y_center, color_tuple)

            # Pass image cv -> tkinter
            _, tmp_file = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmp_file, self.cv_image)  # pylint: disable=c-extension-no-member
            self.image_map = tkinter.PhotoImage(file=tmp_file)
            os.remove(tmp_file)

            # Display on screen
            put_image()

        def reload_callback() -> None:

            # Reload from file
            self.image_map = tkinter.PhotoImage(file=self.map_file)

            # image for cv
            self.cv_image = cv2.imread(self.map_file)  # pylint: disable=c-extension-no-member

            # Display on screen
            put_image()

        def click_callback(event: typing.Any) -> None:

            if not self.fill_mode_selected:
                tkinter.messagebox.showinfo(title="Error", message="Mode to fill is not selected!")
                return

            if self.fill_mode_selected in [FillMode.FILL, FillMode.PAINT] and not self.fill_type_selected:
                tkinter.messagebox.showinfo(title="Error", message="Type to fill is not selected!")
                return

            # Put copy of image in stack
            cv_image_copy = self.cv_image.copy()
            self.images_stack.append(cv_image_copy)

            # Get click position
            x_mouse, y_mouse = event.x, event.y

            if self.fill_mode_selected is FillMode.FILL:
                assert self.fill_type_selected is not None
                color = COLORS_TABLE[self.fill_type_selected]
                color_tuple = tuple(reversed(color.values()))
                cv2.floodFill(self.cv_image, None, (x_mouse, y_mouse), color_tuple)  # pylint: disable=c-extension-no-member

            if self.fill_mode_selected is FillMode.PAINT:
                poly = np.array([
                    (x_mouse - self.thickness_selected, y_mouse - self.thickness_selected),
                    (x_mouse + self.thickness_selected, y_mouse - self.thickness_selected),
                    (x_mouse + self.thickness_selected, y_mouse + self.thickness_selected),
                    (x_mouse - self.thickness_selected, y_mouse + self.thickness_selected)
                ])
                assert self.fill_type_selected is not None
                color = COLORS_TABLE[self.fill_type_selected]
                color_tuple = tuple(reversed(color.values()))
                cv2.fillPoly(self.cv_image, [poly], color_tuple)  # pylint: disable=c-extension-no-member

            if self.fill_mode_selected is FillMode.SPECIAL_COAST:
                color_tuple = COAST_MARKER_COLOR
                hexagon(x_mouse, y_mouse, color_tuple)

            # Pass image cv -> tkinter
            _, tmp_file = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmp_file, self.cv_image)  # pylint: disable=c-extension-no-member
            self.image_map = tkinter.PhotoImage(file=tmp_file)
            os.remove(tmp_file)

            # Display on screen
            put_image()

        def undo_callback() -> None:

            # Must have an image in stack
            if not self.images_stack:
                tkinter.messagebox.showinfo(title="Error", message="Nothing to undo!")
                return

            # Get from stack
            self.cv_image = self.images_stack.pop()

            # Pass image cv -> tkinter
            _, tmp_file = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmp_file, self.cv_image)  # pylint: disable=c-extension-no-member
            self.image_map = tkinter.PhotoImage(file=tmp_file)
            os.remove(tmp_file)

            # Display on screen
            put_image()

        def save_callback() -> None:
            """ Save to file """

            # Save to file
            cv2.imwrite(self.map_file, self.cv_image)  # pylint: disable=c-extension-no-member

        def select_fill_type_callback(fill_type: FillType) -> None:
            """ Change fill type selection """
            self.fill_type_selected = fill_type

        def select_fill_mode_callback(fill_mode: FillMode) -> None:
            """ Change fill mode selection """
            self.fill_mode_selected = fill_mode

        def select_fill_thickness_callback(more: bool) -> None:
            """ Change thickness selection """
            if more:
                if self.thickness_selected >= MAX_THICKNESS:
                    tkinter.messagebox.showinfo(title="Error", message="Too thick!")
                    return
                self.thickness_selected += 1
            else:
                if self.thickness_selected <= 1:
                    tkinter.messagebox.showinfo(title="Error", message="Not thick enough!")
                    return
                self.thickness_selected -= 1
            information = f"{self.thickness_selected} px"
            self.thickness_value.display(information)

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

        # frame buttons
        # -----------

        frame_buttons = tkinter.LabelFrame(main_frame, text="Actions")
        frame_buttons.grid(row=2, column=2, sticky='nw')

        frame_actions_buttons = tkinter.LabelFrame(frame_buttons, text="Main")
        frame_actions_buttons.grid(row=1, column=1, sticky='nw')

        self.reload_button = tkinter.Button(frame_actions_buttons, text="Reload map file", command=reload_callback)
        self.reload_button.grid(row=1, column=1, sticky='we')

        self.undo_button = tkinter.Button(frame_actions_buttons, text="Undo", command=undo_callback)
        self.undo_button.grid(row=2, column=1, sticky='we')

        self.save_button = tkinter.Button(frame_actions_buttons, text="Save", command=save_callback)
        self.save_button.grid(row=3, column=1, sticky='we')

        self.erase_coasts_button = tkinter.Button(frame_actions_buttons, text="Erase coasts zones", command=lambda e=True: coasts_zones_callback(e))  # type: ignore
        self.erase_coasts_button.grid(row=4, column=1, sticky='we')

        self.draw_coasts_button = tkinter.Button(frame_actions_buttons, text="Draw coasts zones", command=lambda e=False: coasts_zones_callback(e))  # type: ignore
        self.draw_coasts_button.grid(row=5, column=1, sticky='we')

        self.erase_centers_button = tkinter.Button(frame_actions_buttons, text="Erase centers", command=lambda e=True: centers_callback(e))  # type: ignore
        self.erase_centers_button.grid(row=6, column=1, sticky='we')

        self.draw_centers_button = tkinter.Button(frame_actions_buttons, text="Draw centers", command=lambda e=False: centers_callback(e))  # type: ignore
        self.draw_centers_button.grid(row=7, column=1, sticky='we')

        frame_selection_type_buttons = tkinter.LabelFrame(frame_buttons, text="Selection fill type")
        frame_selection_type_buttons.grid(row=2, column=1, sticky='nw')

        for num, fill_type in enumerate(FillType):
            self.fill_button = tkinter.Button(frame_selection_type_buttons, text=fill_type.name.title(), command=lambda ft=fill_type: select_fill_type_callback(ft))  # type: ignore
            self.fill_button.grid(row=4 + num, column=1, sticky='we')

        frame_selection_mode_buttons = tkinter.LabelFrame(frame_buttons, text="Selection fill mode")
        frame_selection_mode_buttons.grid(row=3, column=1, sticky='nw')

        self.fill_button = tkinter.Button(frame_selection_mode_buttons, text="Fill", command=lambda fm=FillMode.FILL: select_fill_mode_callback(fm))  # type: ignore
        self.fill_button.grid(row=1, column=1, sticky='we')

        self.paint_button = tkinter.Button(frame_selection_mode_buttons, text="Paint", command=lambda fm=FillMode.PAINT: select_fill_mode_callback(fm))  # type: ignore
        self.paint_button.grid(row=2, column=1, sticky='we')

        self.coast_button = tkinter.Button(frame_selection_mode_buttons, text="Special coast (hexagon)", command=lambda fm=FillMode.SPECIAL_COAST: select_fill_mode_callback(fm))  # type: ignore
        self.coast_button.grid(row=3, column=1, sticky='we')

        frame_selection_paintbrush_buttons = tkinter.LabelFrame(frame_buttons, text="Paintbrush")
        frame_selection_paintbrush_buttons.grid(row=4, column=1, sticky='nw')

        self.smaller_button = tkinter.Button(frame_selection_paintbrush_buttons, text="Smaller paintbrush", command=lambda m=False: select_fill_thickness_callback(m))  # type: ignore
        self.smaller_button.grid(row=1, column=1, sticky='we')

        self.bigger_button = tkinter.Button(frame_selection_paintbrush_buttons, text="Bigger paintbrush", command=lambda m=True: select_fill_thickness_callback(m))  # type: ignore
        self.bigger_button.grid(row=2, column=1, sticky='we')

        self.thickness_label = tkinter.Label(frame_selection_paintbrush_buttons, text="Size of paintbrush :")
        self.thickness_label.grid(row=3, column=1, sticky='we')

        self.thickness_value = MyText(self.master, frame_selection_paintbrush_buttons, height=INFO_HEIGHT, width=INFO_WIDTH)
        self.thickness_value.grid(row=3, column=2, sticky='we')

    def menu_complete_quit(self) -> None:
        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def main_loop(map_file: str, parameters_file: typing.Optional[str]) -> None:
    """ main_loop """

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with map file '{map_file}'...")

    # use description of first register as overall title
    window_name = "Diplomania map editer tool"

    # create app
    root.title(window_name)

    app = Application(map_file, parameters_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_file', required=True, help='Map file to edit')
    parser.add_argument('-p', '--parameters_file', required=False, help='Load a parameters file at start (for erasing special centers)')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file
    parameters_file = args.parameters_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)
    main_loop(map_file, parameters_file)

    print("The End")


if __name__ == "__main__":
    main()
