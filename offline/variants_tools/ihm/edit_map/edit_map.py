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
import shutil
import enum

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

import cv2  # type: ignore


# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

INFO_HEIGHT1 = 3
INFO_WIDTH1 = 30

INFO_HEIGHT2 = 15
INFO_WIDTH2 = 30

BUTTONS_PER_COLUMN = 24

TITLE = "Map editor, select fill type and click on map to fill"

# File with colors
COLORS_FILE_NAME = "./colors.ini"

@enum.unique
class FillType(enum.Enum):
    """ FillType """

    LAND_COAST = enum.auto()
    SEA = enum.auto()
    UNPASSABLE = enum.auto()


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



def load_colors() -> VersionRecord:
    """ load_colors """

    # Where is the file ?
    colors_file = COLORS_FILE_NAME
    assert os.path.isfile(colors_file), f"Please create file {colors_file}"

    config = configparser.ConfigParser()
    config.read(colors_file)

    colors_dict = {}
    for fill_type in FillType:
        colors_dict[fill_type] = {k: int(v) for k,v in dict(config[fill_type.name]).items()}

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

    def __init__(self, map_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # actual creation of widgets
        self.create_widgets(self, map_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str) -> None:
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

            if not self.fill_select:
                tkinter.messagebox.showinfo(title="Error", message="Type to fill is not selected!")
                return

            x_mouse, y_mouse = event.x, event.y

            # Backup file
            shutil.copyfile(self.map_file, self.map_bak_file)

            # Apply
            cv_image = cv2.imread(self.map_file)  # pylint: disable=c-extension-no-member
            color = COLORS_TABLE[self.fill_select]
            color_tuple = tuple(color.values())
            print(f"{color_tuple=}")
            cv2.floodFill(cv_image, None, (x_mouse, y_mouse), color_tuple)
            cv2.imwrite(self.map_file, cv_image)

            # Show changed file
            put_image()

        def reload_callback() -> None:
            put_image()

        def undo_callback() -> None:
            shutil.copyfile(self.map_bak_file, self.map_file)
            os.unlink(self.map_bak_file)
            put_image()

        def select_callback(fill_type: FillType):
            self.fill_select = fill_type

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
        self.map_bak_file = f"{map_file}.bak"
        put_image()

        # frame buttons and information
        # -----------

        self.fill_select = None

        frame_buttons = tkinter.LabelFrame(main_frame, text="Actions")
        frame_buttons.grid(row=2, column=2, sticky='nw')

        self.reload_button = tkinter.Button(frame_buttons, text="Reload map file", command=reload_callback)
        self.reload_button.grid(row=1, column=1, sticky='we')

        self.reload_button = tkinter.Button(frame_buttons, text="Undo", command=undo_callback)
        self.reload_button.grid(row=2, column=1, sticky='we')

        for num, fill_type in enumerate(FillType):
            self.reload_button = tkinter.Button(frame_buttons, text=fill_type.name, command=lambda ft=fill_type: select_callback(ft))
            self.reload_button.grid(row=3 + num, column=1, sticky='we')

    def menu_complete_quit(self) -> None:
        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def main_loop(map_file: str) -> None:
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

    app = Application(map_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_file', required=True,
help='Map file to edit')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)
    main_loop(map_file)

    print("The End")


if __name__ == "__main__":
    main()
