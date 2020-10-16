#!/usr/bin/env python3

"""
an ihm based on tkinter
this is the main module
"""

import typing
import sys
import datetime
import configparser
import collections

import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext  # type: ignore

import requests

import font

SESSION = requests.Session()

HELP_FILE = "./help/help_content.txt"


COLOR_SCROLLED_INFO = 'Black'
COLOR_SCROLLED_WARNING = 'Orange'
COLOR_SCROLLED_ERROR = 'Red'

COLOR_INFO = "Blue"
COLOR_WARNING = 'Purple'

# elements for tooltip
TOOLTIP_HELP_DELAY = 1000
TOOLTIP_X_OFFSET = 20
TOOLTIP_Y_OFFSET = 20
TOOLTIP_FONT = ("tahoma", "8", "normal")
TOOLTIP_COLOR = "Light Yellow"

# some separators are inserted
SEPARATOR_SIZE = 4

TEXT_BACKGROUND = 'Ghost White'

# This is a variable to notify done for this game
QUIT = False

# for checking input
MAX_LEN_NAME = 30

WIDTH_DESC = MAX_LEN_NAME
HEIGHT_DESC = 3

# The token that serves to be identified
JWT_TOKEN = ''


DEFAULT_VARIANT = 'standard'
DEFAULT_VICTORY_CENTERS = 18
DEFAULT_NB_CYCLES = 99
DEFAULT_SPEED_MOVES = 2
DEFAULT_SPEED_OTHERS = 1
DEFAULT_CD_POSSIBLE_MOVES_BUILDS = 0
DEFAULT_CD_OTHERS = 1

GAME_STATE_OPTIONS = {"0": "Attente", "1": "Démarrée", "2": "Terminée"}


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """ Accesses a section of a config file  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """ Accesses the list of sections of a config file  """
        return self._config.sections()


SERVER_CONFIG: typing.Dict[str, typing.Dict[str, typing.Any]] = collections.defaultdict(dict)


def load_servers_config() -> None:
    """ read servers config """

    global SERVER_CONFIG

    servers_config = ConfigFile('./config/servers.ini')
    for server in servers_config.section_list():
        server_data = servers_config.section(server)
        SERVER_CONFIG[server]['HOST'] = server_data['HOST']
        SERVER_CONFIG[server]['PORT'] = int(server_data['PORT'])


class SelectorWidget(tkinter.Frame):
    """ This is a selector it allows choosing amonst values """

    def __init__(self, parent: typing.Any, value_var: typing.Any, type_info: typing.Dict[str, str]):

        tkinter.Frame.__init__(self, parent)
        self.radiobutton_inputs = list()
        for num, (value, text) in enumerate(type_info.items()):
            radiobutton_input = tkinter.Radiobutton(self, variable=value_var, text=text, value=value, indicatoron=1)
            self.radiobutton_inputs.append(radiobutton_input)
            radiobutton_input.grid(row=1 + num, column=1, sticky='w')

    def disable(self) -> None:
        """ disable """
        for radiobutton_input in self.radiobutton_inputs:
            radiobutton_input.config(state=tkinter.DISABLED)

    def enable(self) -> None:
        """ enable """
        for radiobutton_input in self.radiobutton_inputs:
            radiobutton_input.config(state=tkinter.ACTIVE)


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # identification data to send to server
        self.login_var = tkinter.StringVar()
        self.password_var = tkinter.StringVar()

        # game entry
        self.game_name_var = tkinter.StringVar()
        self.variant_name_var = tkinter.StringVar()
        self.variant_name_var.set(DEFAULT_VARIANT)  # type: ignore
        self.archive_var = tkinter.IntVar()

        self.current_state_var = tkinter.IntVar()

        self.anonymous_var = tkinter.IntVar()
        self.silent_var = tkinter.IntVar()
        self.cumulate_var = tkinter.IntVar()

        self.fast_var = tkinter.IntVar()
        self.speed_moves_var = tkinter.IntVar()
        self.cd_possible_moves_var = tkinter.IntVar()
        self.speed_retreats_var = tkinter.IntVar()
        self.cd_possible_retreats_var = tkinter.IntVar()
        self.speed_adjustments_var = tkinter.IntVar()
        self.cd_possible_builds_var = tkinter.IntVar()
        self.cd_possible_removals_var = tkinter.IntVar()
        self.play_weekend_var = tkinter.IntVar()

        self.manual_var = tkinter.IntVar()
        self.access_code_var = tkinter.IntVar()
        self.access_restriction_reliability_var = tkinter.IntVar()
        self.access_restriction_regularity_var = tkinter.IntVar()
        self.access_restriction_performance_var = tkinter.IntVar()

        self.current_advancement_var = tkinter.IntVar()
        self.nb_max_cycles_to_play_var = tkinter.IntVar()
        self.victory_centers_var = tkinter.IntVar()

        self.speed_moves_var.set(DEFAULT_SPEED_MOVES)  # type: ignore
        self.speed_retreats_var.set(DEFAULT_SPEED_OTHERS)  # type: ignore
        self.speed_adjustments_var.set(DEFAULT_SPEED_OTHERS)  # type: ignore

        self.cd_possible_moves_var.set(DEFAULT_CD_POSSIBLE_MOVES_BUILDS)  # type: ignore
        self.cd_possible_retreats_var.set(DEFAULT_CD_OTHERS)  # type: ignore
        self.cd_possible_builds_var.set(DEFAULT_CD_POSSIBLE_MOVES_BUILDS)  # type: ignore
        self.cd_possible_removals_var.set(DEFAULT_CD_OTHERS)  # type: ignore

        self.nb_max_cycles_to_play_var.set(DEFAULT_NB_CYCLES)  # type: ignore
        self.victory_centers_var.set(DEFAULT_VICTORY_CENTERS)  # type: ignore

        # actual creation of widgets
        self.create_widgets(self)

    def create_widgets(self, main_frame: tkinter.Frame) -> None:
        """ create all widgets for application """

        def some_help() -> None:
            help_window = tkinter.Toplevel()
            help_window.title("Un peu d'aide")

            with open(HELP_FILE, 'r', encoding="utf-8") as file_ptr2:
                content = file_ptr2.readlines()
                text = ''.join(content)
                help_text = tkinter.Text(help_window, wrap="word")
                help_text.tag_configure("blue", foreground="blue")
                help_text.grid()
                help_text.insert("1.0", text)  # type: ignore
                ok_button = tkinter.Button(help_window, text='OK', command=help_window.destroy)
                ok_button.grid()

        def about() -> None:
            version_information = "Cette beta version est très incomplète !"
            tkinter.messagebox.showinfo("A propos", str(version_information))

        menu_bar = tkinter.Menu(main_frame)
        menu_file = tkinter.Menu(menu_bar, tearoff=0)

        menu_file.add_separator()  # type: ignore

        menu_file.add_command(label="Recommencer", command=self.menu_restart)  # type: ignore
        menu_file.add_command(label="Sortie", command=self.on_closing)  # type: ignore
        menu_bar.add_cascade(label="Fichier", menu=menu_file)  # type: ignore

        menu_help = tkinter.Menu(menu_bar, tearoff=0)
        menu_help.add_command(label="Un peu d'aide", command=some_help)  # type: ignore
        menu_help.add_command(label="A propos...", command=about)  # type: ignore

        menu_bar.add_cascade(label="Aide", menu=menu_help)  # type: ignore

        self.master.configure(menu=menu_bar)

        frame_title = tkinter.Frame(main_frame)
        frame_title.grid(row=1, column=1, sticky='we')

        # a logo
        photo_diplo = tkinter.PhotoImage(file="./static/logo_diplo.png")
        label_photo = tkinter.Label(frame_title, image=photo_diplo, compound='top')
        label_photo.image = photo_diplo  # type: ignore # keep reference
        label_photo.grid(row=1, column=1, sticky='w')

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=2)

        # login field
        label_login = tkinter.Label(frame_title, text="Login (pseudo) -->")
        label_login.grid(row=1, column=4)
        entry_login_input = tkinter.Entry(frame_title, textvariable=self.login_var)
        entry_login_input.grid(row=1, column=5)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=6)

        # password field
        label_password = tkinter.Label(frame_title, text="Mot de passe -->")
        label_password.grid(row=1, column=7)
        entry_password_input = tkinter.Entry(frame_title, show="*", textvariable=self.password_var)
        entry_password_input.grid(row=1, column=8)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=9)

        # button
        button_login = tkinter.Button(frame_title, text="Login")
        button_login.config(state=tkinter.ACTIVE)
        button_login.bind("<Button-1>", self.callback_login)
        button_login.grid(row=1, column=10)

        paned_up = tkinter.PanedWindow(main_frame)
        paned_up.grid(row=2, column=1)

        # Buttons =======================
        frame_buttons = tkinter.LabelFrame(paned_up, text="Entrée")
        paned_up.add(frame_buttons)  # type: ignore

        # button
        self.button_new = tkinter.Button(frame_buttons, text="Créer une nouvelle partie")
        self.button_new.config(state=tkinter.ACTIVE)
        self.button_new.bind("<Button-1>", self.callback_create_new_game)
        self.button_new.grid(row=20, column=1)

        # button
        self.button_already = tkinter.Button(frame_buttons, text="Charger une partie existante")
        self.button_already.config(state=tkinter.ACTIVE)
        self.button_already.bind("<Button-1>", self.callback_select_game)
        self.button_already.grid(row=20, column=2)

        # EDITION
        paned_middle = tkinter.PanedWindow(main_frame, orient=tkinter.HORIZONTAL)
        paned_middle.grid(row=3, column=1)

        # Main parameters =======================
        frame_parameters_a = tkinter.LabelFrame(paned_middle, text="Paramètres principaux de la partie")
        paned_middle.add(frame_parameters_a)  # type: ignore

        # name field
        label_name = tkinter.Label(frame_parameters_a, text="Nom -->")
        label_name.grid(row=1, column=1, sticky='w')
        self.entry_game_name_input = tkinter.Entry(frame_parameters_a, textvariable=self.game_name_var, width=MAX_LEN_NAME)
        self.entry_game_name_input.grid(row=1, column=2, sticky='w')
        self.entry_game_name_input.config(state=tkinter.DISABLED)

        # description field
        description_name = tkinter.Label(frame_parameters_a, text="Description (*) -->")
        description_name.grid(row=2, column=1, sticky='w')
        self.text_description_input = tkinter.Text(frame_parameters_a, width=WIDTH_DESC, height=HEIGHT_DESC)
        self.text_description_input.grid(row=2, column=2, sticky='w')
        # for linux use Grey85
        self.text_description_input.config(state=tkinter.DISABLED, bg='Grey95')

        # variant field
        label_variant = tkinter.Label(frame_parameters_a, text="Variante -->")
        label_variant.grid(row=3, column=1, sticky='w')
        self.entry_variant_name_input = tkinter.Entry(frame_parameters_a, textvariable=self.variant_name_var, width=MAX_LEN_NAME)
        self.entry_variant_name_input.grid(row=3, column=2, sticky='w')
        self.entry_variant_name_input.config(state=tkinter.DISABLED)

        # cumulable  field
        self.label_archive = tkinter.Label(frame_parameters_a, text="Archive -->")
        self.label_archive.grid(row=4, column=1, sticky='w')
        self.checkbutton_archive = tkinter.Checkbutton(frame_parameters_a, variable=self.archive_var)
        self.checkbutton_archive.grid(row=4, column=2, sticky='w')
        self.checkbutton_archive.config(state=tkinter.DISABLED)

        # current state field
        label_current_state = tkinter.Label(frame_parameters_a, text="Etat courant -->")
        label_current_state.grid(row=5, column=1, sticky='w')
        self.frame_current_state_input = SelectorWidget(frame_parameters_a, self.current_state_var, GAME_STATE_OPTIONS)
        self.frame_current_state_input.disable()
        self.frame_current_state_input.grid(row=5, column=2, sticky='w')

        # Conditions of game =======================
        frame_parameters_b = tkinter.LabelFrame(paned_middle, text="Modalités")
        paned_middle.add(frame_parameters_b)  # type: ignore

        # anonymous  field
        self.label_anonymous = tkinter.Label(frame_parameters_b, text="Anonyme -->")
        self.label_anonymous.grid(row=1, column=1, sticky='w')
        self.checkbutton_anonymous = tkinter.Checkbutton(frame_parameters_b, variable=self.anonymous_var)
        self.checkbutton_anonymous.grid(row=1, column=2, sticky='w')
        self.checkbutton_anonymous.config(state=tkinter.DISABLED)

        # silent  field
        self.label_silent = tkinter.Label(frame_parameters_b, text="Sliencieux -->")
        self.label_silent.grid(row=2, column=1, sticky='w')
        self.checkbutton_silent = tkinter.Checkbutton(frame_parameters_b, variable=self.silent_var)
        self.checkbutton_silent.grid(row=2, column=2, sticky='w')
        self.checkbutton_silent.config(state=tkinter.DISABLED)

        # cumulable  field
        self.label_cumulable = tkinter.Label(frame_parameters_b, text="Cumulable -->")
        self.label_cumulable.grid(row=4, column=1, sticky='w')
        self.checkbutton_cumulable = tkinter.Checkbutton(frame_parameters_b, variable=self.cumulate_var)
        self.checkbutton_cumulable.grid(row=4, column=2, sticky='w')
        self.checkbutton_cumulable.config(state=tkinter.DISABLED)

        # fast  field
        self.label_fast = tkinter.Label(frame_parameters_b, text="Rapide -->")
        self.label_fast.grid(row=5, column=1, sticky='w')
        self.checkbutton_fast = tkinter.Checkbutton(frame_parameters_b, variable=self.fast_var)
        self.checkbutton_fast.grid(row=5, column=2, sticky='w')
        self.checkbutton_fast.config(state=tkinter.DISABLED)

        # Game speed parameters =======================
        frame_parameters_c = tkinter.LabelFrame(paned_middle, text="Cadence de jeu")
        paned_middle.add(frame_parameters_c)  # type: ignore

        # deadline  field
        self.label_deadline = tkinter.Label(frame_parameters_c, text="Date limite (*) -->")
        self.label_deadline.grid(row=1, column=1, sticky='w')
        today = datetime.date.today()
        values = list()
        for offset in range(10):
            new_deadline = today + datetime.timedelta(days=offset)
            values.append(new_deadline)
        self.spin_deadline = tkinter.Spinbox(frame_parameters_c, values=values, width=10)
        self.spin_deadline.grid(row=1, column=2)
        self.spin_deadline.config(state=tkinter.DISABLED)

        # speed_moves  field
        self.label_speed_moves = tkinter.Label(frame_parameters_c, text="Vitesse mouvements (*) -->")
        self.label_speed_moves.grid(row=2, column=1, sticky='w')
        self.entry_speed_moves = tkinter.Entry(frame_parameters_c, textvariable=self.speed_moves_var, width=5)
        self.entry_speed_moves.grid(row=2, column=2, sticky='w')
        self.entry_speed_moves.config(state=tkinter.DISABLED)

        # cd possible moves
        self.label_cd_possible_moves = tkinter.Label(frame_parameters_c, text="D.C. possible sur mouvements -(*) ->")
        self.label_cd_possible_moves.grid(row=3, column=1, sticky='w')
        self.checkbutton_cd_possible_moves = tkinter.Checkbutton(frame_parameters_c, variable=self.cd_possible_moves_var)
        self.checkbutton_cd_possible_moves.grid(row=3, column=2, sticky='w')
        self.checkbutton_cd_possible_moves.config(state=tkinter.DISABLED)

        # speed_retreats  field
        self.label_speed_retreats = tkinter.Label(frame_parameters_c, text="Vitesse retraites (*) -->")
        self.label_speed_retreats.grid(row=4, column=1, sticky='w')
        self.entry_speed_retreats = tkinter.Entry(frame_parameters_c, textvariable=self.speed_retreats_var, width=5)
        self.entry_speed_retreats.grid(row=4, column=2, sticky='w')
        self.entry_speed_retreats.config(state=tkinter.DISABLED)

        # cd possible retreats
        self.label_cd_possible_retreats = tkinter.Label(frame_parameters_c, text="D.C. possible sur retraites (*) -->")
        self.label_cd_possible_retreats.grid(row=5, column=1, sticky='w')
        self.checkbutton_cd_possible_retreats = tkinter.Checkbutton(frame_parameters_c, variable=self.cd_possible_retreats_var)
        self.checkbutton_cd_possible_retreats.grid(row=5, column=2, sticky='w')
        self.checkbutton_cd_possible_retreats.config(state=tkinter.DISABLED)

        # speed_adjustments  field
        self.label_speed_adjustments = tkinter.Label(frame_parameters_c, text="Vitesse ajustements (*) -->")
        self.label_speed_adjustments.grid(row=6, column=1, sticky='w')
        self.entry_speed_adjustments = tkinter.Entry(frame_parameters_c, textvariable=self.speed_adjustments_var, width=5)
        self.entry_speed_adjustments.grid(row=6, column=2, sticky='w')
        self.entry_speed_adjustments.config(state=tkinter.DISABLED)

        # cd possible builds
        self.label_cd_possible_builds = tkinter.Label(frame_parameters_c, text="D.C. possible sur constructions (*) -->")
        self.label_cd_possible_builds.grid(row=7, column=1, sticky='w')
        self.checkbutton_cd_possible_builds = tkinter.Checkbutton(frame_parameters_c, variable=self.cd_possible_builds_var)
        self.checkbutton_cd_possible_builds.grid(row=7, column=2, sticky='w')
        self.checkbutton_cd_possible_builds.config(state=tkinter.DISABLED)

        # cd possible removals
        self.label_cd_possible_removals = tkinter.Label(frame_parameters_c, text="D.C. possible sur suppressions (*) -->")
        self.label_cd_possible_removals.grid(row=8, column=1, sticky='w')
        self.checkbutton_cd_possible_removals = tkinter.Checkbutton(frame_parameters_c, variable=self.cd_possible_removals_var)
        self.checkbutton_cd_possible_removals.grid(row=8, column=2, sticky='w')
        self.checkbutton_cd_possible_removals.config(state=tkinter.DISABLED)

        # play week end  field
        self.label_play_weekends = tkinter.Label(frame_parameters_c, text="Jouée le week-end (*) -->")
        self.label_play_weekends.grid(row=9, column=1, sticky='w')
        self.checkbutton_play_weekends = tkinter.Checkbutton(frame_parameters_c, variable=self.play_weekend_var)
        self.checkbutton_play_weekends.grid(row=9, column=2, sticky='w')
        self.checkbutton_play_weekends.config(state=tkinter.DISABLED)

        # Access parameters =======================
        frame_parameters_d = tkinter.LabelFrame(paned_middle, text="Accès et allocation")
        paned_middle.add(frame_parameters_d)  # type: ignore

        # manual  field
        self.label_manual = tkinter.Label(frame_parameters_d, text="Affectations manuelles (*) -->")
        self.label_manual.grid(row=1, column=1, sticky='w')
        self.checkbutton_manual = tkinter.Checkbutton(frame_parameters_d, variable=self.manual_var)
        self.checkbutton_manual.grid(row=1, column=2, sticky='w')
        self.checkbutton_manual.config(state=tkinter.DISABLED)

        # access code  field
        self.label_access_code = tkinter.Label(frame_parameters_d, text="Code d'accès (*) -->")
        self.label_access_code.grid(row=2, column=1, sticky='w')
        self.entry_access_code = tkinter.Entry(frame_parameters_d, textvariable=self.access_code_var, width=5)
        self.entry_access_code.grid(row=2, column=2, sticky='w')
        self.entry_access_code.config(state=tkinter.DISABLED)

        # reliability restriction  field
        self.label_reliability_restriction = tkinter.Label(frame_parameters_d, text="Restriction fiabilité (**) -->")
        self.label_reliability_restriction.grid(row=3, column=1, sticky='w')
        self.entry_reliability_restriction = tkinter.Entry(frame_parameters_d, textvariable=self.access_restriction_reliability_var, width=5)
        self.entry_reliability_restriction.grid(row=3, column=2, sticky='w')
        self.entry_reliability_restriction.config(state=tkinter.DISABLED)

        # regularity restriction  field
        self.label_regularity_restriction = tkinter.Label(frame_parameters_d, text="Restriction régularité (**) -->")
        self.label_regularity_restriction.grid(row=4, column=1, sticky='w')
        self.entry_regularity_restriction = tkinter.Entry(frame_parameters_d, textvariable=self.access_restriction_regularity_var, width=5)
        self.entry_regularity_restriction.grid(row=4, column=2, sticky='w')
        self.entry_regularity_restriction.config(state=tkinter.DISABLED)

        # performance restriction  field
        self.label_performance_restriction = tkinter.Label(frame_parameters_d, text="Restriction performance (**) -->")
        self.label_performance_restriction.grid(row=5, column=1, sticky='w')
        self.entry_performance_restriction = tkinter.Entry(frame_parameters_d, textvariable=self.access_restriction_performance_var, width=5)
        self.entry_performance_restriction.grid(row=5, column=2, sticky='w')
        self.entry_performance_restriction.config(state=tkinter.DISABLED)

        # Advancement parameters =======================
        frame_parameters_e = tkinter.LabelFrame(paned_middle, text="Avancement")
        paned_middle.add(frame_parameters_e)  # type: ignore

        # current advancement   field
        self.label_current_advancement = tkinter.Label(frame_parameters_e, text="Avancement courant -->")
        self.label_current_advancement.grid(row=1, column=1, sticky='w')
        self.entry_current_advancement = tkinter.Entry(frame_parameters_e, textvariable=self.current_advancement_var, width=5)
        self.entry_current_advancement.grid(row=1, column=2, sticky='w')
        self.entry_current_advancement.config(state=tkinter.DISABLED)

        # max cycle to play   field
        self.label_nb_max_cycles = tkinter.Label(frame_parameters_e, text="Nombre max. de cycles à jouer -->")
        self.label_nb_max_cycles.grid(row=2, column=1, sticky='w')
        self.entry_nb_max_cycles = tkinter.Entry(frame_parameters_e, textvariable=self.nb_max_cycles_to_play_var, width=5)
        self.entry_nb_max_cycles.grid(row=2, column=2, sticky='w')
        self.entry_nb_max_cycles.config(state=tkinter.DISABLED)

        # victory centers   field
        self.label_victory_centers = tkinter.Label(frame_parameters_e, text="Victoire en centres -->")
        self.label_victory_centers.grid(row=3, column=1, sticky='w')
        self.entry_victory_centers = tkinter.Entry(frame_parameters_e, textvariable=self.victory_centers_var, width=5)
        self.entry_victory_centers.grid(row=3, column=2, sticky='w')
        self.entry_victory_centers.config(state=tkinter.DISABLED)

        # INFO
        paned_before_down = tkinter.PanedWindow(main_frame)
        paned_before_down.grid(row=4, column=1)
        frame_info = tkinter.LabelFrame(paned_before_down, text="Informations complémentaires")
        paned_before_down.add(frame_info)  # type: ignore
        label_info_1 = tkinter.Label(frame_info, text="(*) changeable à tout moment")
        label_info_1.grid(row=1, column=1, sticky='w')
        label_info_2 = tkinter.Label(frame_info, text="(**) changeable avant le démarrage de la partie")
        label_info_2.grid(row=2, column=1, sticky='w')

        # ACTION
        paned_down = tkinter.PanedWindow(main_frame)
        paned_down.grid(row=5, column=1)

        # Buttons =======================
        frame_buttons = tkinter.LabelFrame(paned_down, text="Action")
        paned_down.add(frame_buttons)  # type: ignore

        # button
        self.button_create_game = tkinter.Button(frame_buttons, text="Créer la partie avec ces informations")
        self.button_create_game.config(state=tkinter.DISABLED)
        self.button_create_game.bind("<Button-1>", self.callback_create_game)
        self.button_create_game.grid(row=1, column=1)

        # button
        self.button_select_game = tkinter.Button(frame_buttons, text="Sélectionner cette partie")
        self.button_select_game.config(state=tkinter.DISABLED)
        self.button_select_game.bind("<Button-1>", self.callback_reload_game)
        self.button_select_game.grid(row=1, column=2)

        # button
        self.button_modify_game = tkinter.Button(frame_buttons, text="Modifier la partie")
        self.button_modify_game.config(state=tkinter.DISABLED)
        self.button_modify_game.bind("<Button-1>", self.callback_modify_game)
        self.button_modify_game.grid(row=1, column=3)

        # button
        self.button_suppress_game = tkinter.Button(frame_buttons, text="Supprimer la partie")
        self.button_suppress_game.config(state=tkinter.DISABLED)
        self.button_suppress_game.bind("<Button-1>", self.callback_suppress_game)
        self.button_suppress_game.grid(row=1, column=5)

    def reload_from_server(self) -> typing.Tuple[bool, str]:
        """ Reloads everything from server to here """

        name = self.game_name_var.get()  # type: ignore
        host = SERVER_CONFIG['GAME']['HOST']
        port = SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{name}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message

        json_dict = req_result.json()

        # description: special
        prev_state = self.text_description_input.cget("state")  # type: ignore
        self.text_description_input.config(state=tkinter.NORMAL)
        self.text_description_input.insert("1.0", json_dict['description'])  # type: ignore
        self.text_description_input.config(state=prev_state)

        self.variant_name_var.set(json_dict['variant'])  # type: ignore
        self.archive_var.set(json_dict['archive'])  # type: ignore
        self.current_state_var.set(json_dict['current_state'])  # type: ignore
        self.anonymous_var.set(json_dict['anonymous'])  # type: ignore
        self.silent_var.set(json_dict['silent'])  # type: ignore
        self.cumulate_var.set(json_dict['cumulate'])  # type: ignore
        self.fast_var.set(json_dict['fast'])  # type: ignore

        # deadline: special
        prev_state = self.spin_deadline.cget("state")  # type: ignore
        self.spin_deadline.config(state=tkinter.NORMAL)

        deadline_str = json_dict['deadline']
        year, month, day = tuple(map(int, deadline_str.split('-')))
        deadline = datetime.date(year, month, day)
        values = list()
        for offset in range(10):
            new_deadline = deadline + datetime.timedelta(days=offset)
            values.append(new_deadline)

        self.spin_deadline.config(values=values)
        self.spin_deadline.config(state=prev_state)

        self.speed_moves_var.set(json_dict['speed_moves'])  # type: ignore
        self.cd_possible_moves_var.set(json_dict['cd_possible_moves'])  # type: ignore
        self.speed_retreats_var.set(json_dict['speed_retreats'])  # type: ignore
        self.cd_possible_retreats_var.set(json_dict['cd_possible_retreats'])  # type: ignore
        self.speed_adjustments_var.set(json_dict['speed_adjustments'])  # type: ignore
        self.cd_possible_builds_var.set(json_dict['cd_possible_builds'])  # type: ignore
        self.cd_possible_removals_var.set(json_dict['cd_possible_removals'])  # type: ignore
        self.play_weekend_var.set(json_dict['play_weekend'])  # type: ignore
        self.manual_var.set(json_dict['manual'])  # type: ignore
        self.access_code_var.set(json_dict['access_code'])  # type: ignore
        self.access_restriction_reliability_var.set(json_dict['access_restriction_reliability'])  # type: ignore
        self.access_restriction_regularity_var.set(json_dict['access_restriction_regularity'])  # type: ignore
        self.access_restriction_performance_var.set(json_dict['access_restriction_performance'])  # type: ignore
        self.current_advancement_var.set(json_dict['current_advancement'])  # type: ignore
        self.nb_max_cycles_to_play_var.set(json_dict['nb_max_cycles_to_play'])  # type: ignore
        self.victory_centers_var.set(json_dict['victory_centers'])  # type: ignore

        return True, ""

    def upload_on_server(self, new: bool) -> typing.Tuple[bool, str]:
        """ Uploads everything here to server """

        name = self.game_name_var.get()  # type: ignore

        json_dict = {
            'name': name,
            'description': self.text_description_input.get(1.0, tkinter.END),
            'variant': self.variant_name_var.get(),  # type: ignore
            'archive': self.archive_var.get(),  # type: ignore
            'current_state': self.current_state_var.get(),  # type: ignore

            'anonymous': self.anonymous_var.get(),  # type: ignore
            'silent': self.silent_var.get(),  # type: ignore
            'cumulate': self.cumulate_var.get(),  # type: ignore
            'fast': self.fast_var.get(),  # type: ignore

            'deadline': self.spin_deadline.get(),  # type: ignore
            'speed_moves': self.speed_moves_var.get(),  # type: ignore
            'cd_possible_moves': self.cd_possible_moves_var.get(),  # type: ignore
            'speed_retreats': self.speed_retreats_var.get(),  # type: ignore
            'cd_possible_retreats': self.cd_possible_retreats_var.get(),  # type: ignore
            'speed_adjustments': self.speed_adjustments_var.get(),  # type: ignore
            'cd_possible_builds': self.cd_possible_builds_var.get(),  # type: ignore
            'cd_possible_removals': self.cd_possible_removals_var.get(),  # type: ignore
            'play_weekend': self.play_weekend_var.get(),  # type: ignore

            'manual': self.manual_var.get(),  # type: ignore
            'access_code': self.access_code_var.get(),  # type: ignore
            'access_restriction_reliability': self.access_restriction_reliability_var.get(),  # type: ignore
            'access_restriction_regularity': self.access_restriction_regularity_var.get(),  # type: ignore
            'access_restriction_performance': self.access_restriction_performance_var.get(),  # type: ignore

            'current_advancement': self.current_advancement_var.get(),  # type: ignore
            'nb_max_cycles_to_play': self.nb_max_cycles_to_play_var.get(),  # type: ignore
            'victory_centers': self.victory_centers_var.get(),  # type: ignore

            'pseudo': self.login_var.get()  # type: ignore
        }

        if new:
            host = SERVER_CONFIG['GAME']['HOST']
            port = SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/games"
            req_result = SESSION.post(url, data=json_dict, headers={'access_token': JWT_TOKEN})
            if req_result.status_code != 201:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                return False, message
        else:
            host = SERVER_CONFIG['GAME']['HOST']
            port = SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/games/{name}"
            req_result = SESSION.put(url, data=json_dict, headers={'access_token': JWT_TOKEN})
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                return False, message

        return True, ""

    def callback_login(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        # Now I get token
        pseudo = self.login_var.get()  # type: ignore
        password = self.password_var.get()  # type: ignore

        host = SERVER_CONFIG['USER']['HOST']
        port = SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/login-user"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': password})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à l'identification : {message}")
            return

        # very important : extract token for authentication
        json_dict = req_result.json()
        global JWT_TOKEN
        JWT_TOKEN = json_dict['access_token']

        tkinter.messagebox.showinfo("OK", "Identification réussie !")

    def callback_create_new_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.button_new.config(state=tkinter.DISABLED)
        self.button_already.config(state=tkinter.DISABLED)

        self.entry_game_name_input.config(state=tkinter.NORMAL)
        self.text_description_input.config(state=tkinter.NORMAL, bg='White')

        # for the moment we do not handle other variants than standard so safer that way
        #  self.entry_variant_name_input.config(state=tkinter.NORMAL)

        self.frame_current_state_input.enable()
        self.checkbutton_anonymous.config(state=tkinter.NORMAL)
        self.checkbutton_silent.config(state=tkinter.NORMAL)
        self.checkbutton_cumulable.config(state=tkinter.NORMAL)
        self.checkbutton_archive.config(state=tkinter.NORMAL)
        self.checkbutton_fast.config(state=tkinter.NORMAL)
        self.spin_deadline.config(state=tkinter.NORMAL)
        self.entry_speed_moves.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_moves.config(state=tkinter.NORMAL)
        self.entry_speed_retreats.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_retreats.config(state=tkinter.NORMAL)
        self.entry_speed_adjustments.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_builds.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_removals.config(state=tkinter.NORMAL)
        self.checkbutton_play_weekends.config(state=tkinter.NORMAL)
        self.checkbutton_manual.config(state=tkinter.NORMAL)
        self.entry_access_code.config(state=tkinter.NORMAL)
        self.entry_regularity_restriction.config(state=tkinter.NORMAL)
        self.entry_reliability_restriction.config(state=tkinter.NORMAL)
        self.entry_performance_restriction.config(state=tkinter.NORMAL)
        self.entry_nb_max_cycles.config(state=tkinter.NORMAL)
        self.entry_victory_centers.config(state=tkinter.NORMAL)

        self.button_create_game.config(state=tkinter.NORMAL)

    def callback_select_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.button_new.config(state=tkinter.DISABLED)
        self.button_already.config(state=tkinter.DISABLED)

        self.entry_game_name_input.config(state=tkinter.NORMAL)

        self.button_select_game.config(state=tkinter.NORMAL)

    def callback_create_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.upload_on_server(True)
        if not status:
            tkinter.messagebox.showerror("KO", f"La partie n'a pas été créé : {message}")
            return

        tkinter.messagebox.showinfo("OK", "La partie a été créée")

    def callback_reload_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.reload_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Partie inexistante ou autre problème : {message}")
            return

        self.text_description_input.config(state=tkinter.NORMAL, bg='White')
        self.frame_current_state_input.enable()
        self.spin_deadline.config(state=tkinter.NORMAL)
        self.entry_speed_moves.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_moves.config(state=tkinter.NORMAL)
        self.entry_speed_retreats.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_retreats.config(state=tkinter.NORMAL)
        self.entry_speed_adjustments.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_builds.config(state=tkinter.NORMAL)
        self.checkbutton_cd_possible_removals.config(state=tkinter.NORMAL)
        self.checkbutton_play_weekends.config(state=tkinter.NORMAL)

        state = self.current_state_var.get()  # type: ignore

        if state == 0:
            self.checkbutton_manual.config(state=tkinter.NORMAL)
            self.entry_access_code.config(state=tkinter.NORMAL)
            self.button_suppress_game.config(state=tkinter.ACTIVE)

        if state == 1:
            self.entry_regularity_restriction.config(state=tkinter.DISABLED)
            self.entry_reliability_restriction.config(state=tkinter.DISABLED)
            self.entry_performance_restriction.config(state=tkinter.DISABLED)
            self.button_suppress_game.config(state=tkinter.DISABLED)

        if state == 2:
            self.button_suppress_game.config(state=tkinter.ACTIVE)

        self.entry_game_name_input.config(state=tkinter.DISABLED)
        self.button_select_game.config(state=tkinter.DISABLED)
        self.button_modify_game.config(state=tkinter.ACTIVE)

    def callback_modify_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.upload_on_server(False)
        if not status:
            tkinter.messagebox.showerror("KO", f"La partie n'a pas été mise à jour : {message}")
            return

        tkinter.messagebox.showinfo("OK", "La partie a été mise à jour")

    def callback_suppress_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        name = self.game_name_var.get()  # type: ignore
        if len(name) > MAX_LEN_NAME:
            tkinter.messagebox.showerror("KO", f"Votre nom de partie est trop long : {len(name)}")
            return

        if not tkinter.messagebox.askyesno("Attention", "Confimez vous la suppression de la partie ?"):
            return

        status, message = self.reload_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Il y a eu un problème : {message}")
            return

        state = self.current_state_var.get()  # type: ignore
        if state not in [0, 2]:
            tkinter.messagebox.showerror("KO", "La partie n'est pas en attente ou terminée")
            return

        # give pseudo to server to check rights
        json_dict = {
            'pseudo': self.login_var.get()  # type: ignore
        }

        host = SERVER_CONFIG['GAME']['HOST']
        port = SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{name}"
        req_result = SESSION.delete(url, data=json_dict, headers={'access_token': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showwarning("KO", f"Il y a eu un problème (probablement la partie n'existe pas) : {message}")
            return

        self.text_description_input.config(state=tkinter.DISABLED, bg='Grey95')
        self.frame_current_state_input.disable()
        self.checkbutton_fast.config(state=tkinter.DISABLED)
        self.spin_deadline.config(state=tkinter.DISABLED)
        self.entry_speed_moves.config(state=tkinter.DISABLED)
        self.checkbutton_cd_possible_moves.config(state=tkinter.DISABLED)
        self.entry_speed_retreats.config(state=tkinter.DISABLED)
        self.checkbutton_cd_possible_retreats.config(state=tkinter.DISABLED)
        self.entry_speed_adjustments.config(state=tkinter.DISABLED)
        self.checkbutton_cd_possible_builds.config(state=tkinter.DISABLED)
        self.checkbutton_cd_possible_removals.config(state=tkinter.DISABLED)
        self.checkbutton_play_weekends.config(state=tkinter.DISABLED)

        self.button_modify_game.config(state=tkinter.DISABLED)
        self.button_suppress_game.config(state=tkinter.DISABLED)

        tkinter.messagebox.showinfo("OK", "La partie a été supprimée")

    def menu_complete_quit(self) -> None:
        """ as it says """
        global QUIT
        QUIT = True
        self.on_closing()

    def menu_restart(self) -> None:
        """ From menu change context """

        # quit application
        self.master.quit()  # type: ignore

    def on_closing(self) -> None:
        """ User closed window """

        self.master.quit()  # type: ignore
        sys.exit(0)


def main() -> None:
    """ main """

    load_servers_config()

    x_pos, y_pos = 0, 0

    while True:

        root = tkinter.Tk()

        root.geometry(f"+{x_pos}+{y_pos}")
        root.resizable(False, False)

        # font for all widgets
        root.option_add("*Font", f"{font.FONT_USED} {font.FONT_SIZE}")

        # font for tabs too
        style = tkinter.ttk.Style()
        style.configure('TNotebook.Tab', font=(font.FONT_USED, font.FONT_SIZE))

        # use description of first register as overall title
        window_name = "Démonstrateur client IHM création de partie - projet ANJD (Diplomatie)"

        root.title(window_name)

        app = Application(master=root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

        # remember where window is to put new one same place
        x_pos, y_pos = root.winfo_x(), root.winfo_y()  # type: ignore

        del app
        root.destroy()

        if QUIT:
            break


if __name__ == "__main__":
    main()
