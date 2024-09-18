""" training """
# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from math import pi
from json import loads, dumps
from time import time

from browser import html, ajax, alert, document, window   # pylint: disable=import-error

import config
import mydialog
import common
import geometry
import mapping
import interface
import memoize
import variants

# Different trainings
TRAINING_INDEX = 0
TRAINING_LIST = []

# From json file
INTRODUCTION = ""
ROLE_ID = None
VARIANT_NAME_LOADED = None
GAME_PARAMETERS_LOADED = {
    'name': "",
    'description': "",  # to be precised
    'variant': "standard",  # to be precised
    'fog': False,
    'archive': False,
    'used_for_elo': False,
    'manual': False,
    'fast': False,
    'anonymous': False,
    'nomessage_current': False,
    'nopress_current': False,
    'scoring': "CDIP",
    'deadline': 0,  # to be precised
    'deadline_hour': 0,
    'deadline_sync': False,
    'grace_duration': 24,
    'speed_moves': 24,
    'cd_possible_moves': False,
    'speed_retreats': 24,
    'cd_possible_retreats': False,
    'speed_adjustments': 24,
    'cd_possible_builds': False,
    'play_weekend': False,
    'access_restriction_reliability': 0,
    'access_restriction_regularity': 0,
    'access_restriction_performance': 0,
    'current_advancement': 1,  # to be precised
    'nb_max_cycles_to_play': 7,
    'current_state': 1,
    'game_type': 0,
    'finished': False,
    'soloed': False
}
TUNED_GAME_PARAMETERS_LOADED = None
GAME_STATUS = None
POSITION_LOADED = None
POSITION_DATA = None
EXPECTED_ORDERS = None
SHOWN_ORDERS = None

POINTERS = []

HELP = ""

SEQUENCE_NAME = ""

# constant
ORDERS_LOADED = {'fake_units': [], 'orders': []}

# from load_static_stuff()
VARIANT_CONTENT_LOADED = None
INTERFACE_CHOSEN = None
INTERFACE_PARAMETERS_READ = None
VARIANT_DATA = None

MY_PANEL = html.DIV()
MY_SUB_PANEL = html.DIV(id="page")
MY_SUB_PANEL.attrs['style'] = 'display: table-row'
MY_PANEL <= MY_SUB_PANEL

ARRIVAL = None


def set_arrival(arrival):
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = arrival


class AutomatonStateEnum:
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = 1
    SELECT_ORDER_STATE = 2
    SELECT_PASSIVE_UNIT_STATE = 3
    SELECT_DESTINATION_STATE = 4
    SELECT_BUILD_UNIT_TYPE_STATE = 5


class AutomatonStateEnum2:
    """ AutomatonStateEnum2 """

    SELECT_ACTION_STATE = 1
    SELECT_POSITION_STATE = 2
    SELECT_UNIT_STATE = 3


# canvas backup to optimize drawing map when only orders change
BACKUP_CANVAS = None


def save_context(ctx):
    """ save_context """

    global BACKUP_CANVAS

    # create backup canvas
    BACKUP_CANVAS = html.CANVAS(width=ctx.canvas.width, height=ctx.canvas.height)
    bctx = BACKUP_CANVAS.getContext("2d")

    # copy canvas into it
    bctx.drawImage(ctx.canvas, 0, 0)


def restore_context(ctx):
    """ restore_context """

    ctx.drawImage(BACKUP_CANVAS, 0, 0)


def get_trainings_list():
    """ get_trainings_list """

    trainings_list = {}

    def reply_callback(req):
        nonlocal trainings_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des entraînements : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des entraînements : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        trainings_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/trainings-list"

    # getting trainings list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return trainings_list


def get_training(training_name):
    """ get_training """

    training = {}

    def reply_callback(req):
        nonlocal training
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de l'entraînement : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de l'entraînement : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        training = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/trainings/{training_name}"

    # getting training list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return training


def next_previous_training(previous: bool):
    """ next_previous_training """
    global TRAINING_INDEX

    if previous:
        if TRAINING_INDEX <= 0:
            return
        TRAINING_INDEX -= 1
    else:
        if TRAINING_INDEX >= len(TRAINING_LIST) - 1:
            return
        TRAINING_INDEX += 1

    # go for next training
    install_training()


def reset_training_callback(ev):  # pylint: disable=invalid-name
    """ reset_training_callback """
    ev.preventDefault()
    MY_SUB_PANEL.clear()
    select_training_data()


def reload_text_callback(ev):  # pylint: disable=invalid-name
    """ reload_text_callback """
    ev.preventDefault()
    mydialog.InfoDialog("Information", INTRODUCTION, True)


def ask_help_callback(ev):  # pylint: disable=invalid-name
    """ ask_help_callback """
    ev.preventDefault()
    alert(HELP)


def get_game_status():
    """ get_game__status """

    def show_variant_callback(ev, variant_name):  # pylint: disable=invalid-name
        """ show_variant_callback """

        ev.preventDefault()

        arrival = 'variant'

        # so that will go to proper page
        variants.set_arrival(arrival, variant_name)

        # action of going to game page
        PANEL_MIDDLE.clear()
        variants.render(PANEL_MIDDLE)

    description = GAME_PARAMETERS_LOADED['description']
    game_variant = GAME_PARAMETERS_LOADED['variant']

    advancement_loaded = GAME_PARAMETERS_LOADED['current_advancement']
    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    game_season = common.get_full_season(advancement_loaded, VARIANT_DATA, nb_max_cycles_to_play, True)

    game_status_table = html.TABLE()

    row = html.TR()

    # reset
    form = html.FORM()
    input_reset_training = html.INPUT(type="submit", value="reset", Class='btn-inside')
    input_reset_training.attrs['style'] = 'font-size: 10px'
    input_reset_training.bind("click", reset_training_callback)
    form <= input_reset_training
    col = html.TD(form)
    row <= col

    # title
    col = html.TD(html.I(SEQUENCE_NAME))
    row <= col

    # indicator
    col = html.TD(f"{TRAINING_INDEX + 1}/{len(TRAINING_LIST)}")
    row <= col

    # season
    col = html.TD(f"Saison {game_season}")
    row <= col

    # variant + link
    form = html.FORM()
    input_show_variant = html.INPUT(type="submit", value=game_variant, Class='btn-inside')
    input_show_variant.attrs['style'] = 'font-size: 10px'
    input_show_variant.bind("click", lambda e, v=game_variant: show_variant_callback(e, v))
    form <= input_show_variant
    col = html.TD(form)
    row <= col

    game_status_table <= row

    row = html.TR()

    form = ""
    if TRAINING_INDEX > 0:
        form = html.FORM()
        input_previous_training = html.INPUT(type="submit", value="planche précédente", Class='btn-inside')
        input_previous_training.attrs['style'] = 'font-size: 10px'
        input_previous_training.bind("click", lambda e: next_previous_training(True))
        form <= input_previous_training
    col = html.TD(form)
    row <= col

    # reload
    form = html.FORM()
    input_help = html.INPUT(type="submit", value="Ré-afficher l'explication", Class='btn-inside')
    input_help.attrs['style'] = 'font-size: 10px'
    input_help.bind("click", reload_text_callback)
    form <= input_help
    col = html.TD(form)
    row <= col

    # help
    form = ""
    if HELP:
        form = html.FORM()
        input_help = html.INPUT(type="submit", value="un peu d'aide", Class='btn-inside')
        input_help.attrs['style'] = 'font-size: 10px'
        input_help.bind("click", ask_help_callback)
        form <= input_help
    col = html.TD(form)
    row <= col

    col = html.TD(html.B(description))
    row <= col

    form = ""
    if TRAINING_INDEX < len(TRAINING_LIST) - 1:
        form = html.FORM()
        input_next_training = html.INPUT(type="submit", value="planche suivante", Class='btn-inside')
        input_next_training.attrs['style'] = 'font-size: 10px'
        input_next_training.bind("click", lambda e: next_previous_training(False))
        form <= input_next_training
    col = html.TD(form)
    row <= col

    game_status_table <= row

    return game_status_table


def stack_role_flag(frame):
    """ stack_role_flag """

    # role flag
    role = VARIANT_DATA.roles[ROLE_ID]
    role_name = VARIANT_DATA.role_name_table[role]
    role_icon_img = common.display_flag(VARIANT_NAME_LOADED, INTERFACE_CHOSEN, ROLE_ID, role_name)
    frame <= role_icon_img
    frame <= html.BR()
    frame <= html.BR()


def stack_role_retreats(frame):
    """ stack_role_retreats """
    role = VARIANT_DATA.roles[ROLE_ID]
    info_retreats = POSITION_DATA.role_retreats(role)
    for info_retreat in info_retreats:
        frame <= html.DIV(info_retreat, Class='note')
        frame <= html.BR()


def stack_role_builds(frame):
    """ stack_role_builds """
    role = VARIANT_DATA.roles[ROLE_ID]
    nb_builds, nb_ownerships, nb_units, nb_free_centers = POSITION_DATA.role_builds(role)
    free_info = f" et {nb_free_centers} emplacement(s) libre(s)" if nb_ownerships > nb_units else ""
    frame <= html.DIV(f"Vous avez {nb_ownerships} centre(s) pour {nb_units} unité(s){free_info}. Vous {'construisez' if nb_builds >= 0 else 'détruisez'} donc {abs(nb_builds)} fois.", Class='note')


def stack_possibilities(frame, advancement_season):
    """ stack_possibilities """

    # : we alert about retreat possibilities
    if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        stack_role_retreats(frame)
        frame <= html.BR()
        frame <= html.BR()

    # first time : we alert about build stat
    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        stack_role_builds(frame)
        frame <= html.BR()
        frame <= html.BR()


def make_rating_colours_window(variant_data, position_data, interface_):
    """ make_rating_window """

    ratings1 = position_data.role_ratings()
    units = position_data.role_units()
    colours = position_data.role_colours()

    rating_table = html.TABLE()

    # flags
    rolename2role_id = {variant_data.role_name_table[v]: k for k, v in variant_data.roles.items()}
    variant_name = variant_data.name
    flags_row = html.TR()
    rating_table <= flags_row
    col = html.TD(html.B("Drapeaux :"))
    flags_row <= col
    for role_name in ratings1:
        col = html.TD()
        role_id = rolename2role_id[role_name]
        role_icon_img = common.display_flag(variant_name, interface_, role_id, role_name)
        col <= role_icon_img
        flags_row <= col

    # roles
    rating_names_row = html.TR()
    rating_table <= rating_names_row
    col = html.TD(html.B("Rôles :"))
    rating_names_row <= col
    for role_name in ratings1:
        col = html.TD()

        canvas2 = html.CANVAS(id="rect", width=15, height=15, alt=role_name)
        ctx2 = canvas2.getContext("2d")

        colour = colours[role_name]

        outline_colour = colour.outline_colour()
        ctx2.strokeStyle = outline_colour.str_value()
        ctx2.lineWidth = 2
        ctx2.beginPath()
        ctx2.rect(0, 0, 14, 14)
        ctx2.stroke()
        ctx2.closePath()  # no fill

        ctx2.fillStyle = colour.str_value()
        ctx2.fillRect(1, 1, 13, 13)

        col <= canvas2
        col <= f" {role_name}"
        rating_names_row <= col

    # centers
    rating_centers_row = html.TR()
    rating_table <= rating_centers_row
    col = html.TD(html.B("Centres (unités) :"))
    rating_centers_row <= col
    for role, ncenters in ratings1.items():
        nunits = units[role]
        col = html.TD()
        if nunits != ncenters:
            col <= f"{ncenters} ({nunits})"
        else:
            col <= f"{ncenters}"
        rating_centers_row <= col

    return rating_table


def load_static_stuff():
    """ load_static_stuff : loads global data """

    # from game name get variant name

    # from variant name get variant content

    global VARIANT_CONTENT_LOADED

    # optimization
    if VARIANT_NAME_LOADED in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
        VARIANT_CONTENT_LOADED = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[VARIANT_NAME_LOADED]
    else:
        VARIANT_CONTENT_LOADED = common.game_variant_content_reload(VARIANT_NAME_LOADED)
        if not VARIANT_CONTENT_LOADED:
            alert("Erreur chargement contenu variante")
            return
        memoize.VARIANT_CONTENT_MEMOIZE_TABLE[VARIANT_NAME_LOADED] = VARIANT_CONTENT_LOADED

    # selected interface (user choice)
    global INTERFACE_CHOSEN
    INTERFACE_CHOSEN = interface.get_interface_from_variant(VARIANT_NAME_LOADED)

    # from display chose get display parameters

    global INTERFACE_PARAMETERS_READ

    # optimization
    if (VARIANT_NAME_LOADED, INTERFACE_CHOSEN) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
        INTERFACE_PARAMETERS_READ = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)]
    else:
        INTERFACE_PARAMETERS_READ = common.read_parameters(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)] = INTERFACE_PARAMETERS_READ

    # build variant data
    global VARIANT_DATA

    # optimization
    if (VARIANT_NAME_LOADED, INTERFACE_CHOSEN) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
        VARIANT_DATA = memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)]
    else:
        VARIANT_DATA = mapping.Variant(VARIANT_NAME_LOADED, VARIANT_CONTENT_LOADED, INTERFACE_PARAMETERS_READ)
        memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)] = VARIANT_DATA


def same_orders(orders1, orders2):
    """same_orders"""

    # same if write same
    return sorted(map(str, orders1.orders)) == sorted(map(str, orders2.orders))


def load_dynamic_stuff():
    """ load_dynamic_stuff : loads global data """

    # now game parameters (dynamic since advancement is dynamic)
    GAME_PARAMETERS_LOADED['variant'] = VARIANT_NAME_LOADED
    GAME_PARAMETERS_LOADED['description'] = TUNED_GAME_PARAMETERS_LOADED['title']
    GAME_PARAMETERS_LOADED['current_advancement'] = TUNED_GAME_PARAMETERS_LOADED['game_parameters_current_advancement']
    GAME_PARAMETERS_LOADED['deadline'] = int(time()) + 5 * 60

    global GAME_STATUS
    GAME_STATUS = get_game_status()

    # digest the position
    global POSITION_DATA
    POSITION_DATA = mapping.Position(POSITION_LOADED, VARIANT_DATA)


def slide_just_display():
    """ slide_just_display """

    selected_hovered_object = None

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # unhightlite previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                helper <= selected_hovered_object.description()
            else:
                helper <= "_"

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(prev_selected_hovered_object, mapping.Unit):
                if prev_selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[prev_selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        # hightlite object where mouse is
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, True)
            helper <= selected_hovered_object.description()
        else:
            helper <= "_"

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:

            selected_hovered_object.highlite(ctx, False)

            # redraw all arrows
            orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            POSITION_DATA.render(ctx)

            # put the legends
            VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # pointers
        draw_pointers(ctx)

        # put the orders
        orders_data.render(ctx)

    def draw_pointers(ctx):
        """ draw_pointers """

        ctx.lineWidth = 2
        for pointer in POINTERS:
            x_pos, y_pos = pointer['center']
            ray = pointer['ray']
            red, green, blue = pointer['color']
            pointer_colour = mapping.ColourRecord(red, green, blue)
            ctx.strokeStyle = pointer_colour.str_value()
            ctx.beginPath()
            ctx.arc(x_pos, y_pos, ray, 0, 2 * pi, False)
            ctx.stroke()
            ctx.closePath()

    def put_submit_next(buttons_right):
        """ put_submit_next """

        input_submit = html.INPUT(type="submit", value="La suite !", Class='btn-inside')
        input_submit.bind("click", lambda e: next_previous_training(False))
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # digest the orders
    orders_data = mapping.Orders(ORDERS_LOADED, POSITION_DATA, False)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    rating_colours_window = make_rating_colours_window(VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    display_left <= html.BR()
    display_left <= rating_colours_window
    display_left <= html.BR()

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    # All there is is a button "Ok next please"
    put_submit_next(buttons_right)

    # advertise
    url = f"https://diplomania-gen.fr?sequence={SEQUENCE_NAME}"
    MY_SUB_PANEL <= f"Pour inviter un joueur à réaliser cette séquence, lui envoyer le lien : '{url}'"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= my_sub_panel2


def slide_submit_orders():
    """ slide_submit_orders : ask user to submit orders and check they are correct """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_unit_type = None
    selected_build_zone = None
    selected_hovered_object = None
    automaton_state = None
    buttons_right = None

    def cancel_submit_orders_callback(_, dialog):
        dialog.close(None)

    def submit_orders_callback(_, warned=False, dialog2=None):
        """ submit_orders_callback """

        def reply_callback(req):

            if req:
                req_result = loads(req.text)
                if req.status != 201:
                    if 'message' in req_result:
                        alert(f"Erreur à la soumission d'ordres d'entrainenemt : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la soumission d'ordres d'entrainenemt : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                # use a strip to remove trailing "\n"
                messages = "<br>".join(req_result['submission_report'].strip().split('\n'))

                if messages:
                    mydialog.InfoDialog("Information", f"Ordres validés avec le(s) message(s) : {messages}", True)
                else:
                    mydialog.InfoDialog("Information", "Ordres validés !")

            # compare with expected orders
            expected = mapping.Orders(EXPECTED_ORDERS, POSITION_DATA, False)
            if same_orders(orders_data, expected):
                mydialog.InfoDialog("Information", "Félicitations, ce sont bien les ordres attendus !<br><br>(On passe automatiquement à la planche suivante)", False)
                next_previous_training(False)
            else:
                mydialog.InfoDialog("Information", "Hélas non, ce ne sont pas les ordres attendus :-(", True)

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            role = VARIANT_DATA.roles[ROLE_ID]
            nb_builds, _, _, _ = POSITION_DATA.role_builds(role)
            if nb_builds > 0:
                nb_builds_done = orders_data.number()
                if nb_builds_done < nb_builds:
                    if not warned:
                        dialog = mydialog.Dialog(f"Vous construisez {nb_builds_done} unités alors que vous avez droit à {nb_builds} unités. Vous êtes sûr ?", ok_cancel=True)
                        dialog.ok_button.bind("click", lambda e, w=True, d=dialog: submit_orders_callback(e, w, d))
                        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_submit_orders_callback(e, d))
                        return

        if dialog2:
            dialog2.close()

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        # situation
        situation_dict = {
            'ownerships': POSITION_DATA.save_json2(),
            'dislodged_ones': POSITION_DATA.save_json3(),
            'units': POSITION_DATA.save_json(),
            'forbiddens': POSITION_DATA.save_json4(),
        }

        situation_dict_json = dumps(situation_dict)

        # orders
        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        json_dict = {
            'advancement': GAME_PARAMETERS_LOADED['current_advancement'],
            'variant_name': VARIANT_NAME_LOADED,
            'names': names_dict_json,
            'situation': situation_dict_json,
            'orders': orders_list_dict_json,
            'role_id': ROLE_ID
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/training"

        # submitting position and orders for training : do not need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # to stop catching keyboard
        document.unbind("keypress")

        # complete orders
        orders_data.rest_hold(ROLE_ID)

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        stack_role_flag(buttons_right)

        # information retreats/builds
        stack_possibilities(buttons_right, advancement_season)

        # we are in spring or autumn
        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        stack_role_flag(buttons_right)

        # information retreats/builds
        stack_possibilities(buttons_right, advancement_season)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum.inventory():
                if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)

        # do not put erase all
        if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def select_built_unit_type_callback(_, build_unit_type):
        """ select_built_unit_type_callback """

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state is AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            # role flag
            stack_role_flag(buttons_right)

            # information retreats/builds
            stack_possibilities(buttons_right, advancement_season)

            legend_select_active = html.DIV("Sélectionner la zone où construire", Class='instruction')
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        # to stop catching keyboard
        document.unbind("keypress")

        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER and nb_builds < 0:
                alert("Bien essayé, mais vous devez détruire !")
                return

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER and nb_builds > 0:
                alert("Bien essayé, mais vous devez construire !")
                return

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            stack_role_flag(buttons_right)

            # information retreats/builds
            stack_possibilities(buttons_right, advancement_season)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de la retraite", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:

                legend_select_active = html.DIV("Sélectionner le type d'unité à construire", Class='instruction')
                buttons_right <= legend_select_active

                for unit_type in mapping.UnitTypeEnum.inventory():
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.unit_name_table[unit_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_active = html.DIV("Sélectionner l'unité à retirer", Class='instruction')
                buttons_right <= legend_select_active

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.RETREAT_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_active_unit = POSITION_DATA.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = POSITION_DATA.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            stack_role_flag(buttons_right)

            # information retreats/builds
            stack_possibilities(buttons_right, advancement_season)

            if selected_active_unit is None or selected_active_unit.role != VARIANT_DATA.roles[ROLE_ID]:

                alert("Bien essayé, mais pas d'unité ici ou cette unité ne vous appartient pas ou vous n'avez pas d'ordre à valider.")

                selected_active_unit = None

                # switch back to initial state selecting unit
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit

                    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit
                    for order_type in mapping.OrderTypeEnum.inventory():
                        if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                            input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                            buttons_right <= html.BR()
                            input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                            buttons_right <= html.BR()
                            buttons_right <= input_select

                    automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            else:

                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                    legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                    buttons_right <= legend_selected_unit

                    legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                    buttons_right <= legend_select_order
                    buttons_right <= html.BR()

                    legend_select_order21 = html.I("Raccourcis clavier :")
                    buttons_right <= legend_select_order21
                    buttons_right <= html.BR()

                    for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre"]:
                        legend_select_order22 = html.I(info)
                        buttons_right <= legend_select_order22
                        buttons_right <= html.BR()

                # to catch keyboard
                document.bind("keypress", callback_keypress)

                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, None)
                    orders_data.insert_order(order)

                    # update map
                    callback_render(False)

                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_dest_zone = VARIANT_DATA.closest_zone(pos)
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = VARIANT_DATA.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            stack_role_flag(buttons_right)

            # information retreats/builds
            stack_possibilities(buttons_right, advancement_season)

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.DISBAND_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:
                # create fake unit
                region = selected_build_zone.region
                center = region.center
                if center is None:
                    alert("Bien essayé, mais il n'y a pas de centre à cet endroit !")
                elif region in POSITION_DATA.occupant_table:
                    alert("Bien essayé, mais il y a déjà une unité à cet endroit !")
                elif center not in POSITION_DATA.owner_table:
                    alert("Bien essayé, mais ce centre n'appartient à personne !")
                else:
                    # becomes tricky
                    accepted = True
                    deducted_role = POSITION_DATA.owner_table[center].role
                    if ROLE_ID == 0:  # game master
                        if not VARIANT_CONTENT_LOADED['build_everywhere']:
                            expected_role = center.owner_start
                            if not expected_role:
                                alert("Bien essayé mais ce n'est pas un centre de départ !")
                                accepted = False
                            elif expected_role is not deducted_role:
                                alert("Bien essayé mais ce n'est pas une variante dans laquelle on peut construire partout !")
                                accepted = False
                    else:  # player
                        if ROLE_ID is not deducted_role.identifier:
                            alert("Bien essayé, mais ce centre ne vous appartient pas ")
                            accepted = False
                        elif not VARIANT_CONTENT_LOADED['build_everywhere']:
                            expected_role = center.owner_start
                            if not expected_role:
                                alert("Bien essayé mais ce n'est pas un centre de départ !")
                                accepted = False
                            elif expected_role is not deducted_role:
                                alert("Bien essayé mais ce n'est pas une variante dans laquelle on peut construire partout !")
                                accepted = False
                    if accepted:  # actual build
                        if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                            fake_unit = mapping.Army(POSITION_DATA, deducted_role, selected_build_zone, None, False)
                        if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                            fake_unit = mapping.Fleet(POSITION_DATA, deducted_role, selected_build_zone, None, False)
                        # create order
                        order = mapping.Order(POSITION_DATA, selected_order_type, fake_unit, None, None)
                        orders_data.insert_order(order)

            # update map
            callback_render(False)

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            stack_role_flag(buttons_right)

            # information retreats/builds
            stack_possibilities(buttons_right, advancement_season)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                    put_rest_hold(buttons_right)
                if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    buttons_right <= html.BR()
                    put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_dblclick(event):
        """
        called when there is a double click or when pressing 'x' in which case a None is passed
        """

        nonlocal automaton_state
        nonlocal buttons_right

        # the aim is to give this variable a value
        selected_erase_unit = None

        # first : take from event
        if event:

            # where is the click
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            # moves : select unit : easy case
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_erase_unit = POSITION_DATA.closest_unit(pos, False)

            # retreat : select dislodged unit : easy case
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_erase_unit = POSITION_DATA.closest_unit(pos, True)

            #  builds : tougher case : we take the build units into account
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_erase_unit = orders_data.closest_unit_or_built_unit(pos)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # unit must have an order
        if not orders_data.is_ordered(selected_erase_unit):
            return

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        stack_role_flag(buttons_right)

        # information retreats/builds
        stack_possibilities(buttons_right, advancement_season)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum.inventory():
                if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # unhightlite previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                helper <= selected_hovered_object.description()
            else:
                helper <= "_"

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(prev_selected_hovered_object, mapping.Unit):
                if prev_selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[prev_selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        # hightlite object where mouse is
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, True)
            helper <= selected_hovered_object.description()
        else:
            helper <= "_"

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:

            selected_hovered_object.highlite(ctx, False)

            # redraw all arrows
            orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order removal : special
        if char == 'x':
            # pass to double click
            callback_canvas_dblclick(None)
            return

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            POSITION_DATA.render(ctx)

            # put the legends
            VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # put the orders
        orders_data.render(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        orders = html.DIV()
        for line in lines:
            orders <= html.B(line)
            orders <= html.BR()
        buttons_right <= orders

        # capture the units without an order
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:

            # list units without orders
            unordered_units = [u for u in POSITION_DATA.units if u.role.identifier == ROLE_ID and not orders_data.is_ordered(u)]

            # if there are display them
            if unordered_units:
                buttons_right <= html.BR()
                lines = map(str, unordered_units)
                no_orders = html.DIV()
                for line in lines:
                    no_orders <= html.EM(line)
                    no_orders <= html.BR()
                buttons_right <= no_orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="Effacer tout", Class='btn-inside')
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_rest_hold(buttons_right):
        """ put_rest_hold """

        input_rest_hold = html.INPUT(type="submit", value="Tout le reste tient", Class='btn-inside')
        input_rest_hold.bind("click", rest_hold_callback)
        buttons_right <= html.BR()
        buttons_right <= input_rest_hold
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="Soumettre", Class='btn-inside')
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    advancement_loaded = GAME_PARAMETERS_LOADED['current_advancement']
    advancement_season, _ = common.get_short_season(advancement_loaded, VARIANT_DATA)

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # click and double click
    canvas.bind("click", callback_canvas_click)
    canvas.bind("dblclick", callback_canvas_dblclick)

    # digest the orders
    orders_data = mapping.Orders(ORDERS_LOADED, POSITION_DATA, False)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    rating_colours_window = make_rating_colours_window(VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN)

    # left side
    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    display_left <= html.BR()
    display_left <= rating_colours_window
    display_left <= html.BR()

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # role flag
    stack_role_flag(buttons_right)

    # information retreats/builds
    stack_possibilities(buttons_right, advancement_season)

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    nb_builds = 0
    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:

        # take a note of build / remove
        role = VARIANT_DATA.roles[ROLE_ID]
        nb_builds, _, _, _ = POSITION_DATA.role_builds(role)

        legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_order
        for order_type in mapping.OrderTypeEnum.inventory():
            if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                buttons_right <= html.BR()
                input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                buttons_right <= html.BR()
                buttons_right <= input_select
        automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    if not orders_data.all_ordered(ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        put_rest_hold(buttons_right)
    if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        buttons_right <= html.BR()
        put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    # advertise
    url = f"https://diplomania-gen.fr?sequence={SEQUENCE_NAME}"
    MY_SUB_PANEL <= f"Pour inviter un joueur à réaliser cette séquence, lui envoyer le lien : '{url}'"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= my_sub_panel2


def slide_show_adjudication():
    """ slide_show_adjudication """

    selected_hovered_object = None
    input_submit = None
    report_window = None

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            nonlocal report_window
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres d'entrainenemt : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres d'entrainenemt : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            if 'orders_result' in req_result:

                # remove button
                buttons_right.removeChild(input_submit)

                # say where is adjudication reult
                legend_adjudication_result_location = html.DIV("Le resultat de la résolution est sous la carte.", Class='instruction')
                buttons_right <= legend_adjudication_result_location

                # put new
                time_stamp_now = time()
                report_txt = req_result['orders_result']
                fake_report_loaded = {'time_stamp': time_stamp_now, 'content': report_txt}
                report_window = common.make_report_window(fake_report_loaded)
                display_left <= html.BR()
                display_left <= report_window

            # put button for next
            put_submit_next(buttons_right)

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        # situation
        situation_dict = {
            'ownerships': POSITION_DATA.save_json2(),
            'dislodged_ones': POSITION_DATA.save_json3(),
            'units': POSITION_DATA.save_json(),
            'forbiddens': POSITION_DATA.save_json4(),
        }

        situation_dict_json = dumps(situation_dict)

        # orders
        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        json_dict = {
            'advancement': GAME_PARAMETERS_LOADED['current_advancement'],
            'variant_name': VARIANT_NAME_LOADED,
            'names': names_dict_json,
            'situation': situation_dict_json,
            'orders': orders_list_dict_json,
            'role_id': ROLE_ID
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/training"

        # submitting position and orders for training : do not need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # unhightlite previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                helper <= selected_hovered_object.description()
            else:
                helper <= "_"

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(prev_selected_hovered_object, mapping.Unit):
                if prev_selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[prev_selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        # hightlite object where mouse is
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, True)
            helper <= selected_hovered_object.description()
        else:
            helper <= "_"

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:

            selected_hovered_object.highlite(ctx, False)

            # redraw all arrows
            orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in POSITION_DATA.dislodging_table:
                    dislodged = POSITION_DATA.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            POSITION_DATA.render(ctx)

            # put the legends
            VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # put the orders
        orders_data.render(ctx)

    def put_submit_next(buttons_right):
        """ put_submit_next """

        input_submit = html.INPUT(type="submit", value="La suite !", Class='btn-inside')
        input_submit.bind("click", lambda e: next_previous_training(False))
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """
        nonlocal input_submit

        input_submit = html.INPUT(type="submit", value="Demander la résolution", Class='btn-inside')
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    time_stamp_now = time()
    fake_report_loaded = {'time_stamp': time_stamp_now, 'content': ""}
    report_window = common.make_report_window(fake_report_loaded)

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # digest the orders
    orders_data = mapping.Orders(SHOWN_ORDERS, POSITION_DATA, False)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    rating_colours_window = make_rating_colours_window(VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    display_left <= html.BR()
    display_left <= rating_colours_window
    display_left <= html.BR()

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    # advertise
    url = f"https://diplomania-gen.fr?sequence={SEQUENCE_NAME}"
    MY_SUB_PANEL <= f"Pour inviter un joueur à réaliser cette séquence, lui envoyer le lien : '{url}'"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= my_sub_panel2


def install_training():
    """ install_training """

    global INTRODUCTION
    global ROLE_ID
    global VARIANT_NAME_LOADED
    global EXPECTED_ORDERS
    global SHOWN_ORDERS
    global POINTERS
    global HELP
    global POSITION_LOADED
    global TUNED_GAME_PARAMETERS_LOADED

    content_dict = TRAINING_LIST[TRAINING_INDEX]

    # the role for the trainee
    INTRODUCTION = content_dict['introduction']

    # the variant we use
    VARIANT_NAME_LOADED = content_dict['variant_name']

    # the position
    POSITION_LOADED = content_dict['position']

    # tuned parameters
    TUNED_GAME_PARAMETERS_LOADED = {k: v for k, v in content_dict.items() if k in ['title', 'game_parameters_current_advancement']}

    HELP = content_dict.get('help', '')

    load_static_stuff()
    load_dynamic_stuff()

    # Popup
    mydialog.InfoDialog("Information", INTRODUCTION, True)

    # display map and order console
    MY_SUB_PANEL.clear()

    # consider passive and active mode
    if content_dict['type'] == 'display':
        # pointers to show on map
        POINTERS = content_dict.get('pointers', [])
        slide_just_display()
    elif content_dict['type'] == 'submit':
        ROLE_ID = content_dict['role_id']
        # orders expected from trainee
        EXPECTED_ORDERS = content_dict['expected_orders']
        slide_submit_orders()
    elif content_dict['type'] == 'adjudicate':
        ROLE_ID = 0
        # orders to show
        SHOWN_ORDERS = content_dict['shown_orders']
        slide_show_adjudication()
    else:
        alert("Type de tranche inconnu")


def select_training_data():
    """ select_training_data """

    def load_sequence_callback(ev, input_sequence_name):  # pylint: disable=invalid-name
        """ load_sequence_callback """

        global TRAINING_LIST
        global TRAINING_INDEX
        global SEQUENCE_NAME

        if ev is not None:
            ev.preventDefault()

        content = get_training(input_sequence_name)

        if not content:
            alert("No training data !")
            return

        TRAINING_LIST = content['slides']
        TRAINING_INDEX = 0

        SEQUENCE_NAME = input_sequence_name

        # go for first training
        install_training()

    def load_file_callback(ev, input_file):  # pylint: disable=invalid-name
        """ load_file_callback """

        def onload_callback(_):
            """ onload_callback """

            global TRAINING_LIST
            global TRAINING_INDEX

            content_json = reader.result
            content = loads(content_json)
            TRAINING_LIST = content['slides']
            TRAINING_INDEX = 0

            # go for first training
            install_training()

        ev.preventDefault()

        if not input_file.files:
            alert("Pas de fichier")

            # back to where we started
            MY_SUB_PANEL.clear()
            select_training_data()
            return

        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Extract the file
        file_name = input_file.files[0]
        # Read the file content as text
        reader.bind("load", onload_callback)
        reader.readAsText(file_name)

    trainings_list = get_trainings_list()

    global ARRIVAL
    if ARRIVAL:
        sequence_name = ARRIVAL
        ARRIVAL = None
        load_sequence_callback(None, sequence_name)
        return

    MY_SUB_PANEL <= html.H3("Choisissez un tutoriel, une séquence d'entrainement ou un défi...")

    trainings_table = html.TABLE()

    for title, name in sorted(trainings_list.items(), key=lambda t: t[0]):

        row = html.TR()

        col = html.TD()
        col <= title
        row <= col

        col = html.TD()

        form = html.FORM()
        input_load_training_sequence = html.INPUT(type="submit", value=name, Class='btn-inside')
        input_load_training_sequence.bind("click", lambda e, n=name: load_sequence_callback(e, n))
        form <= input_load_training_sequence
        col <= form

        row <= col

        trainings_table <= row

    MY_SUB_PANEL <= trainings_table

    if common.check_admin():

        MY_SUB_PANEL <= html.H3("Séléction de fichier pour la mise au point")

        form = html.FORM()

        fieldset = html.FIELDSET()
        legend_name = html.LEGEND("Ficher JSON")
        fieldset <= legend_name
        form <= fieldset

        input_file = html.INPUT(type="file", accept='.json', Class='btn-inside')
        form <= input_file
        form <= html.BR()
        form <= html.BR()

        input_load_training_file = html.INPUT(type="submit", value="Charger le fichier", Class='btn-inside')
        input_load_training_file.bind("click", lambda e, i=input_file: load_file_callback(e, i))
        form <= input_load_training_file

        MY_SUB_PANEL <= form


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_SUB_PANEL.clear()
    select_training_data()
    panel_middle <= MY_SUB_PANEL
