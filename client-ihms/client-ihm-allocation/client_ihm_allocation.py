#!/usr/bin/env python3

"""
an ihm based on tkinter
this is the main module
"""

import typing
import sys
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

# The token that serves to be identified
JWT_TOKEN = ''


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

        self.selectable_input_player_list: typing.List[int] = list()
        self.selectable_output_player_list: typing.List[int] = list()
        self.selectable_game_list: typing.List[int] = list()

        self.game_master_var = tkinter.StringVar()

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
        self.button_new = tkinter.Button(frame_buttons, text="Réaliser  des appariements")
        self.button_new.config(state=tkinter.ACTIVE)
        self.button_new.bind("<Button-1>", self.callback_select_game)
        self.button_new.grid(row=1, column=1)

        # EDITION
        paned_middle = tkinter.PanedWindow(main_frame, orient=tkinter.HORIZONTAL)
        paned_middle.grid(row=3, column=1)

        # Game selection =======================
        frame_game_selection = tkinter.LabelFrame(paned_middle, text="Choix de la partie dans laquelle apparier")
        paned_middle.add(frame_game_selection)  # type: ignore

        # game selection field
        label_variant = tkinter.Label(frame_game_selection, text="Partie :")
        label_variant.grid(row=1, column=1, sticky='w')

        self.listbox_selectable_game_input = tkinter.Listbox(frame_game_selection, width=40, exportselection=0)
        self.listbox_selectable_game_input.grid(row=2, column=1, sticky='w')
        self.listbox_selectable_game_input.config(state=tkinter.DISABLED)

        # button
        self.button_select_game = tkinter.Button(frame_game_selection, text="Choisir cette partie")
        self.button_select_game.config(state=tkinter.DISABLED)
        self.button_select_game.bind("<Button-1>", self.callback_start_pairings)
        self.button_select_game.grid(row=2, column=3)

        # Actual matching =======================

        # ACTION
        paned_down = tkinter.PanedWindow(main_frame, orient=tkinter.HORIZONTAL)
        paned_down.grid(row=4, column=1)

        frame_actual_matching = tkinter.LabelFrame(paned_down, text="Appariement")
        paned_down.add(frame_actual_matching)  # type: ignore

        # player selection field
        label_name = tkinter.Label(frame_actual_matching, text="Joueur à ajouter dans la partie:")
        label_name.grid(row=1, column=1, sticky='w')

        self.listbox_selectable_input_player = tkinter.Listbox(frame_actual_matching, width=40, exportselection=0)
        self.listbox_selectable_input_player.grid(row=2, column=1, rowspan=2, sticky='w')
        self.listbox_selectable_input_player.config(state=tkinter.DISABLED)

        # button
        self.button_insert_pairing = tkinter.Button(frame_actual_matching, text="->")
        self.button_insert_pairing.config(state=tkinter.DISABLED)
        self.button_insert_pairing.bind("<Button-1>", self.callback_put_in)
        self.button_insert_pairing.grid(row=2, column=2)

        # button
        self.button_remove_pairing = tkinter.Button(frame_actual_matching, text="<-")
        self.button_remove_pairing.config(state=tkinter.DISABLED)
        self.button_remove_pairing.bind("<Button-1>", self.callback_remove_from)
        self.button_remove_pairing.grid(row=3, column=2)

        # player selection field
        label_name = tkinter.Label(frame_actual_matching, text="Joueur à retirer de la partie")
        label_name.grid(row=1, column=3, sticky='w')

        self.listbox_selectable_output_player = tkinter.Listbox(frame_actual_matching, width=40, exportselection=0)
        self.listbox_selectable_output_player.grid(row=2, column=3, rowspan=2, sticky='w')
        self.listbox_selectable_output_player.config(state=tkinter.DISABLED)

        # GM Info =======================

        # ACTION
        paned_downer = tkinter.PanedWindow(main_frame, orient=tkinter.HORIZONTAL)
        paned_downer.grid(row=5, column=1)

        frame_game_master_info = tkinter.LabelFrame(paned_downer, text="Note")
        paned_downer.add(frame_game_master_info)  # type: ignore

        # game master
        label_name = tkinter.Label(frame_game_master_info, text="Arbitre de la partie -->")
        label_name.grid(row=1, column=1, sticky='w')

        self.fake_entry_gm_input = tkinter.Entry(frame_game_master_info, textvariable=self.game_master_var)
        self.fake_entry_gm_input.grid(row=1, column=2)
        self.fake_entry_gm_input.config(state=tkinter.DISABLED)

    def load_games_from_server(self) -> typing.Tuple[bool, str]:
        """ Reloads games from server to here """

        # get all games
        host = SERVER_CONFIG['GAME']['HOST']
        port = SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message

        # show them for selection
        self.selectable_game_list = list()
        json_dict = req_result.json()
        previous_state = self.listbox_selectable_game_input.cget("state")  # type: ignore
        self.listbox_selectable_game_input.config(state=tkinter.NORMAL)
        self.listbox_selectable_game_input.delete(0, tkinter.END)
        for identifier, name in json_dict.items():
            self.selectable_game_list.append(identifier)
            self.listbox_selectable_game_input.insert(tkinter.END, name)  # type: ignore
        self.listbox_selectable_game_input.selection_set(0)  # First
        self.listbox_selectable_game_input.config(state=previous_state)

        self.button_new.config(state=tkinter.DISABLED)

        return True, ""

    def reload_players_from_server(self) -> typing.Tuple[bool, str]:
        """ Reloads players from server to here """

        # get all players
        host = SERVER_CONFIG['PLAYER']['HOST']
        port = SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message
        json_dict = req_result.json()
        player_dict = json_dict

        # get all allocations of the game
        game_index_sel, = self.listbox_selectable_game_input.curselection()  # type: ignore
        game_id = self.selectable_game_list[game_index_sel]
        host = SERVER_CONFIG['GAME']['HOST']
        port = SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{game_id}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message
        json_dict = req_result.json()
        allocations_dict = json_dict

        # who goes left and who goes right
        addables = sorted(set(player_dict.keys()) - set(allocations_dict.keys()), key=lambda i: player_dict[i])
        removables = sorted([k for k, v in allocations_dict.items() if v == -1], key=lambda i: player_dict[i])
        game_masters = sorted([k for k, v in allocations_dict.items() if v == 0], key=lambda i: player_dict[i])

        if game_masters:
            identifier = game_masters[0]
            pseudo = player_dict[identifier]
            self.game_master_var.set(pseudo)  # type: ignore

        # show them for selection (input)
        self.selectable_input_player_list = list()
        previous_state = self.listbox_selectable_input_player.cget("state")  # type: ignore
        self.listbox_selectable_input_player.config(state=tkinter.NORMAL)
        self.listbox_selectable_input_player.delete(0, tkinter.END)
        for identifier in addables:
            pseudo = player_dict[identifier]
            self.selectable_input_player_list.append(identifier)
            self.listbox_selectable_input_player.insert(tkinter.END, pseudo)  # type: ignore
        self.listbox_selectable_input_player.selection_set(0)  # First
        self.listbox_selectable_input_player.config(state=previous_state)

        # show them for selection (output)
        self.selectable_output_player_list = list()
        previous_state = self.listbox_selectable_output_player.cget("state")  # type: ignore
        self.listbox_selectable_output_player.config(state=tkinter.NORMAL)
        self.listbox_selectable_output_player.delete(0, tkinter.END)
        for identifier in removables:
            pseudo = player_dict[identifier]
            self.selectable_output_player_list.append(identifier)
            self.listbox_selectable_output_player.insert(tkinter.END, pseudo)  # type: ignore
        self.listbox_selectable_output_player.selection_set(0)  # First
        self.listbox_selectable_output_player.config(state=previous_state)

        # deactivate impossible buttons
        if self.listbox_selectable_input_player.size():  # type: ignore
            self.button_insert_pairing.config(state=tkinter.ACTIVE)
        else:
            self.button_insert_pairing.config(state=tkinter.DISABLED)

        if self.listbox_selectable_output_player.size():  # type: ignore
            self.button_remove_pairing.config(state=tkinter.ACTIVE)
        else:
            self.button_remove_pairing.config(state=tkinter.DISABLED)

        return True, ""

    def upload_match_on_server(self, put: bool) -> typing.Tuple[bool, str]:
        """ Uploads everything here to server """

        game_index_sel, = self.listbox_selectable_game_input.curselection()  # type: ignore
        game_id = self.selectable_game_list[game_index_sel]

        if put:
            player_index_sel, = self.listbox_selectable_input_player.curselection()  # type: ignore
            player_id = self.selectable_input_player_list[player_index_sel]
        else:
            player_index_sel, = self.listbox_selectable_output_player.curselection()  # type: ignore
            player_id = self.selectable_output_player_list[player_index_sel]

        json_dict = {
            'game_id': game_id,
            'player_id': player_id,
            'role_id': -1,
            'pseudo': self.login_var.get()  # type: ignore
        }

        host = SERVER_CONFIG['GAME']['HOST']
        port = SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"
        if put:
            req_result = SESSION.post(url, data=json_dict, headers={'access_token': JWT_TOKEN})
            if req_result.status_code != 201:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                return False, message
        else:
            req_result = SESSION.delete(url, data=json_dict, headers={'access_token': JWT_TOKEN})
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
        url = f"{host}:{port}/login"
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

    def callback_select_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.load_games_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Problème : {message}")
            return

        self.listbox_selectable_game_input.config(state=tkinter.NORMAL)
        self.button_select_game.config(state=tkinter.NORMAL)

    def callback_start_pairings(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.reload_players_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Problème : {message}")
            return

        self.listbox_selectable_input_player.config(state=tkinter.NORMAL)
        self.listbox_selectable_output_player.config(state=tkinter.NORMAL)

        # deactivate impossible buttons
        if self.listbox_selectable_input_player.size():  # type: ignore
            self.button_insert_pairing.config(state=tkinter.ACTIVE)
        else:
            self.button_insert_pairing.config(state=tkinter.DISABLED)

        if self.listbox_selectable_output_player.size():  # type: ignore
            self.button_remove_pairing.config(state=tkinter.ACTIVE)
        else:
            self.button_remove_pairing.config(state=tkinter.DISABLED)

    def callback_put_in(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.upload_match_on_server(True)
        if not status:
            tkinter.messagebox.showerror("KO", f"L'appariement n'a pas été ajouté : {message}")
            return

        status, message = self.reload_players_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Problème : {message}")
            return

        tkinter.messagebox.showinfo("OK", "L'appariement a été ajouté")

    def callback_remove_from(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        status, message = self.upload_match_on_server(False)
        if not status:
            tkinter.messagebox.showerror("KO", f"L'appariement n'a pas été retiré : {message}")
            return

        status, message = self.reload_players_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Problème : {message}")
            return

        tkinter.messagebox.showinfo("OK", "L'appariement a été retiré")

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
        window_name = "Démonstrateur client IHM appariement - projet ANJD (Diplomatie)"

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
