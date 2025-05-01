""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import interface
import mapping
import memoize
import variants
import ratings
import technical
import mydialog
import mypopup
import play_other  # circular import
import play  # circular import


PANEL_MIDDLE = None

# global data below

# loaded in render()
GAME = None
GAME_ID = None
PSEUDO = None
ROLE_ID = None
IN_GAME = False

# loaded in load_static_stuff
PLAYERS_DICT = None
ID2PSEUDO = None
VARIANT_NAME_LOADED = None
VARIANT_CONTENT_LOADED = None
INTERFACE_CHOSEN = None
INTERFACE_PARAMETERS_READ = None
VARIANT_DATA = None
INFORCED_VARIANT_DATA = None

# loaded in load_dynamic_stuff
GAME_PARAMETERS_LOADED = {}
GAME_STATUS = None
POSITION_LOADED = None
POSITION_DATA = None
REPORT_LOADED = {}

# loaded in load_special_stuff
GAME_MASTER = None
GAME_PLAYERS_DICT = {}


def game_votes_reload(game_id):
    """ game_votes_reload """

    votes = None

    def reply_callback(req):
        nonlocal votes
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des votes d'arrêt de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des votes d'arrêt de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        votes = req_result['votes']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-votes/{game_id}"

    # extracting vote from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return votes


def get_roles_submitted_orders(game_id):
    """ get_roles_submitted_orders : returns empty dict if problem """

    submitted_data = {}

    def reply_callback(req):
        nonlocal submitted_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles qui ont soumis des ordres pour la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles qui ont soumis des ordres pour la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        submitted_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders-submitted/{game_id}"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return submitted_data


def game_transition_fog_of_war_reload(game_id, advancement, role_id):
    """ game_transition_fog_of_war_reload : returns empty dict if problem (or no data) """

    transition_loaded = {}

    def reply_callback(req):
        nonlocal transition_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la transition (brouillard) de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la transition (brouillard) de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transition_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-fog-of-war-transitions/{game_id}/{advancement}/{role_id}"

    # getting variant : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return transition_loaded


def game_transition_reload(game_id, advancement):
    """ game_transition_reload : returns empty dict if problem (or no data) """

    transition_loaded = {}

    def reply_callback(req):
        nonlocal transition_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la transition de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la transition de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transition_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}/{advancement}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return transition_loaded


def cancel_last_adjudication_callback(_):
    """ cancel_last_adjudication_callback """

    def reply_callback(req):
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la demande d'annulation de dernière résolution de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la demande d'annulation de dernière résolution de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        messages = "<br>".join(req_result['msg'].split('\n'))
        alert(f"Dernière résolution effacée : {messages}!")
        load_dynamic_stuff()

        MY_SUB_PANEL.clear()
        play.load_option(None, 'Consulter')

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-cancel-last-adjudication/{GAME_ID}"

    # cancel last adjudication a game : need token
    ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def load_static_stuff():
    """ load_static_stuff : loads global data """

    # need to be first since used in get_game_status() and in get_game_master()
    # get the players (all players)
    global PLAYERS_DICT
    PLAYERS_DICT = common.get_players()
    if not PLAYERS_DICT:
        alert("Erreur chargement info joueurs")
        return

    global ID2PSEUDO
    ID2PSEUDO = {v: k for k, v in PLAYERS_DICT.items()}

    # from game name get variant name

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    global VARIANT_NAME_LOADED
    VARIANT_NAME_LOADED = storage['GAME_VARIANT']

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

    # now for official map

    # like above
    interface_inforced = interface.get_inforced_interface_from_variant(VARIANT_NAME_LOADED)

    # optimization
    if (VARIANT_NAME_LOADED, interface_inforced) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
        inforced_interface_parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)]
    else:
        inforced_interface_parameters_read = common.read_parameters(VARIANT_NAME_LOADED, interface_inforced)
        memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)] = inforced_interface_parameters_read

    # build variant data
    global INFORCED_VARIANT_DATA

    # optimization
    if (VARIANT_NAME_LOADED, interface_inforced) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
        INFORCED_VARIANT_DATA = memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)]
    else:
        INFORCED_VARIANT_DATA = mapping.Variant(VARIANT_NAME_LOADED, VARIANT_CONTENT_LOADED, inforced_interface_parameters_read)
        memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)] = INFORCED_VARIANT_DATA

    # get the game master
    global GAME_MASTER
    GAME_MASTER = ""

    game_master_id = common.get_game_master(GAME_ID)
    if game_master_id is not None:
        GAME_MASTER = ID2PSEUDO[game_master_id]


def load_dynamic_stuff():
    """ load_dynamic_stuff : loads global data """

    # now game parameters (dynamic since advancement is dynamic)
    global GAME_PARAMETERS_LOADED
    GAME_PARAMETERS_LOADED = common.game_parameters_reload(GAME)
    if not GAME_PARAMETERS_LOADED:
        alert("Erreur chargement paramètres")
        return

    global GAME_STATUS
    GAME_STATUS = get_game_status()

    # get the position from server
    global POSITION_LOADED
    fog_of_war = GAME_PARAMETERS_LOADED['fog']
    if fog_of_war:
        POSITION_LOADED = common.game_position_fog_of_war_reload(GAME_ID, ROLE_ID)
    else:
        POSITION_LOADED = common.game_position_reload(GAME_ID)
    if not POSITION_LOADED:
        alert("Erreur chargement position")
        return

    # digest the position
    global POSITION_DATA
    POSITION_DATA = mapping.Position(POSITION_LOADED, VARIANT_DATA)

    # need to be after game parameters (advancement -> season)
    global REPORT_LOADED
    fog_of_war = GAME_PARAMETERS_LOADED['fog']
    if fog_of_war:
        REPORT_LOADED = game_fog_of_war_report_reload(GAME_ID, ROLE_ID)
    else:
        REPORT_LOADED = game_report_reload(GAME_ID)

    # REPORT_LOADED can be none


def load_special_stuff():
    """ load_special_stuff : loads global data """

    global GAME_PLAYERS_DICT
    GAME_PLAYERS_DICT = {}

    if PSEUDO is None:
        return

    if ROLE_ID is not None:
        content_loaded = common.game_note_reload(GAME_ID)
        if content_loaded:
            mydialog.InfoDialog("Information", "Attention, vous avez pris des notes dans cette partie !")

    if not (ROLE_ID == 0 or not GAME_PARAMETERS_LOADED['anonymous']):
        return

    # get the players of the game
    # need a token for this
    GAME_PLAYERS_DICT = common.get_game_players_data(GAME_ID)
    if not GAME_PLAYERS_DICT:
        alert("Erreur chargement joueurs de la partie")
        return


def stack_last_moves_button(frame):
    """ stack_last_moves_button """

    def last_moves_callback(ev):  # pylint: disable=invalid-name
        """ last_moves_callback """

        def callback_render(ev):  # pylint: disable=invalid-name
            """ callback_render """
            ev.preventDefault()
            ctx.drawImage(img, 0, 0)
            position_data.render(ctx)
            VARIANT_DATA.render(ctx)
            orders_data.render(ctx)

        def otherwise_callback(ev):  # pylint: disable=invalid-name
            """ real procedure """
            ev.preventDefault()
            play_other.show_position(adv_last_moves)

        ev.preventDefault()

        # calculate last advancement
        last_advancement = GAME_PARAMETERS_LOADED['current_advancement']
        adv_last_moves = last_advancement
        while True:
            adv_last_moves -= 1
            if adv_last_moves % 5 in [0, 2]:
                break

        # image
        advancement_selected = adv_last_moves
        map_size = VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        fog_of_war = GAME_PARAMETERS_LOADED['fog']
        if fog_of_war:
            transition_loaded = game_transition_fog_of_war_reload(GAME_ID, advancement_selected, ROLE_ID)
        else:
            transition_loaded = game_transition_reload(GAME_ID, advancement_selected)
        position_loaded = transition_loaded['situation']
        position_data = mapping.Position(position_loaded, VARIANT_DATA)
        orders_loaded = transition_loaded['orders']
        communication_orders_loaded = transition_loaded['communication_orders']
        orders_data = mapping.Orders(orders_loaded, position_data, communication_orders_loaded)
        img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        img.bind('load', callback_render)

        # content
        content = None

        # otherwise button
        button = html.INPUT(type="submit", value="Sinon, directement...", Class='btn-inside')
        button.bind('click', otherwise_callback)

        popup = mypopup.Popup("Derniers mouvements", canvas, content, button, False)
        frame <= popup

    first_advancement = 0
    if VARIANT_CONTENT_LOADED['start_build']:
        first_advancement = 4

    if GAME_PARAMETERS_LOADED['current_advancement'] == first_advancement:
        return

    input_last_moves = html.INPUT(type="submit", value="Derniers mouvements", Class='btn-inside')
    input_last_moves.bind("click", last_moves_callback)

    frame <= input_last_moves
    frame <= html.BR()
    frame <= html.BR()


# we show only message not older that that
SELECT_DAYS = 10


def stack_last_agreements_button(frame):
    """ stack_last_agreements_button """

    def last_agreements_callback(ev):  # pylint: disable=invalid-name
        """ last_agreements_callback """

        def messages_reload(game_id):
            """ messages_reload """

            messages = []

            def reply_callback(req):
                nonlocal messages
                req_result = loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la récupération des messages dans la partie (derniers messages) : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la récupération des messages dans la partie (derniers messages) : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = req_result['messages_list']

            json_dict = {}

            host = config.SERVER_CONFIG['GAME']['HOST']
            port = config.SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/game-messages/{game_id}"

            # extracting messages from a game : need token (or not?)
            ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

            return messages

        def otherwise_callback(ev):  # pylint: disable=invalid-name
            """ real procedure """

            ev.preventDefault()

            # so that will go to proper page
            arrival = "messages"
            play.set_arrival(arrival)

            # action of going to game page
            PANEL_MIDDLE.clear()
            play.render(PANEL_MIDDLE)

        ev.preventDefault()

        canvas = None

        content = html.DIV()

        messages = messages_reload(GAME_ID)

        time_stamp_now = time()

        # select horizontally only last week
        messages = [m for m in messages if m[2] > time_stamp_now - SELECT_DAYS * 24 * 3600]

        # select vertically only most important fields
        messages = [(m[1], m[3], m[4]) for m in sorted(messages, key=lambda m: m[2], reverse=True)]

        messages_table = html.TABLE()

        thead = html.THEAD()
        for title in ['Auteur', 'Destinataire(s)', 'Contenu']:
            col = html.TD(html.B(title))
            thead <= col
        messages_table <= thead

        for from_role_id_msg, dest_role_id_msgs, the_content in messages:

            row = html.TR()

            col = html.TD()
            role = VARIANT_DATA.roles[from_role_id_msg]
            role_name = VARIANT_DATA.role_name_table[role]
            col <= role_name
            row <= col

            col = html.TD()
            for dest_role_id_msg in dest_role_id_msgs:
                role = VARIANT_DATA.roles[dest_role_id_msg]
                role_name = VARIANT_DATA.role_name_table[role]
                col <= role_name
                col <= " "
            row <= col

            col = html.TD()
            for line in the_content.split('\n'):
                col <= line
                col <= html.BR()
            row <= col

            messages_table <= row

        content <= html.B(f"Depuis moins de {SELECT_DAYS} jours !")
        content <= html.BR()
        content <= messages_table

        # otherwise button
        button = html.INPUT(type="submit", value="Sinon, directement...", Class='btn-inside')
        button.bind('click', otherwise_callback)

        # This popup is the only one resizeable
        popup = mypopup.Popup("Derniers messages", canvas, content, button, True)
        frame <= popup

    if GAME_PARAMETERS_LOADED['nomessage_current']:
        return

    input_last_agreements = html.INPUT(type="submit", value="Derniers messages", Class='btn-inside')
    input_last_agreements.bind("click", last_agreements_callback)
    frame <= input_last_agreements
    frame <= html.BR()
    frame <= html.BR()


def stack_my_orders(frame):
    """ stack_my_orders """

    def my_orders_callback(ev):  # pylint: disable=invalid-name
        """ my_orders_callback """

        def callback_render(ev):  # pylint: disable=invalid-name
            """ callback_render """
            ev.preventDefault()
            ctx.drawImage(img, 0, 0)
            POSITION_DATA.render(ctx)
            orders_data.render(ctx)

        def otherwise_callback(ev):  # pylint: disable=invalid-name
            """ real procedure """
            ev.preventDefault()
            play.load_option(ev, 'Ordonner')

        ev.preventDefault()

        # image
        map_size = VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        orders_loaded = game_orders_reload(GAME_ID)
        orders_data = mapping.Orders(orders_loaded, POSITION_DATA, [])
        img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        img.bind('load', callback_render)

        # content
        content = None

        # otherwise button
        button = html.INPUT(type="submit", value="Sinon, directement...", Class='btn-inside')
        button.bind('click', otherwise_callback)

        popup = mypopup.Popup("Mes ordres", canvas, content, button, False)
        frame <= popup

    # not for game master
    if ROLE_ID == 0:
        return

    input_my_orders = html.INPUT(type="submit", value="Mes ordres", Class='btn-inside')
    input_my_orders.bind("click", my_orders_callback)

    frame <= input_my_orders
    frame <= html.BR()
    frame <= html.BR()


def stack_communications_orders_button(frame):
    """ stack_communications_orders_button """

    def communications_orders_callback(ev):  # pylint: disable=invalid-name
        """ communications_orders_callback """

        def callback_render(ev):  # pylint: disable=invalid-name
            """ callback_render """
            ev.preventDefault()
            ctx.drawImage(img, 0, 0)
            POSITION_DATA.render(ctx)
            orders_data.render(ctx)

        def otherwise_callback(ev):  # pylint: disable=invalid-name
            """ real procedure """
            ev.preventDefault()
            play.load_option(ev, 'Ordres de com\'')

        ev.preventDefault()

        # image
        map_size = VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        communication_orders_loaded = game_communication_orders_reload(GAME_ID)
        orders_data = mapping.Orders(communication_orders_loaded, POSITION_DATA, [])
        img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        img.bind('load', callback_render)

        # content
        content = None

        # otherwise button
        button = html.INPUT(type="submit", value="Sinon, directement...", Class='btn-inside')
        button.bind('click', otherwise_callback)

        popup = mypopup.Popup("Mes ordres de com'", canvas, content, button, False)
        frame <= popup

    if GAME_PARAMETERS_LOADED['game_type'] not in [1, 3]:  # Blitz
        return

    if GAME_PARAMETERS_LOADED['fog']:  # Fog
        return

    input_communications_orders = html.INPUT(type="submit", value="Mes ordres de com' (pour montrer une intention)", Class='btn-inside')
    input_communications_orders.bind("click", communications_orders_callback)
    frame <= input_communications_orders
    frame <= html.BR()
    frame <= html.BR()


def stack_explanations_button(frame):
    """ stack_explanations_button """

    def show_option_callback(ev):  # pylint: disable=invalid-name
        """ show_option_callback """

        ev.preventDefault()

        # so that will go to proper page
        technical.set_arrival('communication')

        # action of going to game page
        PANEL_MIDDLE.clear()
        technical.render(PANEL_MIDDLE)

    input_explanations = html.INPUT(type="submit", value="Explications sur les ordres de com'", Class='btn-inside')
    input_explanations.bind("click", show_option_callback)

    # so that will go to proper page
    frame <= input_explanations
    frame <= html.BR()
    frame <= html.BR()


def stack_cancel_last_adjudication_button(frame):
    """ stack_cancel_last_adjudication_button """

    input_erase = html.INPUT(type="submit", value="Effacer dernière résolution", Class='btn-inside')
    input_erase.bind("click", cancel_last_adjudication_callback)
    frame <= input_erase
    frame <= html.BR()
    frame <= html.BR()


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
    if ROLE_ID != 0:
        role = VARIANT_DATA.roles[ROLE_ID]
        info_retreats = POSITION_DATA.role_retreats(role)
        for info_retreat in info_retreats:
            frame <= html.DIV(info_retreat, Class='note')
            frame <= html.BR()


def stack_role_builds(frame):
    """ stack_role_builds """
    if ROLE_ID != 0:
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


def stack_communication_possibilities(frame, orders_data):
    """ stack_possibilities """

    # No orders : do not know
    if not orders_data.orders:
        frame <= html.DIV("Attention : Vos ordres n'étant pas soumis, impossible de vous rappeler les ordres compatibles (tenir ou se disperser)", Class='note')
        frame <= html.BR()
        frame <= html.BR()
        return

    # Get possible units
    possible_units = [o.active_unit for o in orders_data.orders if o.order_type in [mapping.OrderTypeEnum.HOLD_ORDER, mapping.OrderTypeEnum.DISBAND_ORDER]]

    # none avaiklable
    if not possible_units:
        frame <= html.DIV("Attention : Aucune de vos unité n'a reçu d'ordre *réel* compatible (tenir ou se disperser)", Class='note')
        frame <= html.BR()
        frame <= html.BR()
        return

    #  we alert about comm orders  possibilities
    frame <= html.DIV("Des ordres de communication sont possibles pour les unités suivantes qui ont des ordres *rééls* compatibles (tenir ou se disperser):", Class='note')
    for unit in possible_units:
        frame <= html.DIV(str(unit), Class='note')
    frame <= html.BR()
    frame <= html.BR()


def civil_disorder_allowed(advancement_loaded):
    """ civil_disorder_allowed """

    advancement_season, _ = common.get_short_season(advancement_loaded, VARIANT_DATA)

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        return GAME_PARAMETERS_LOADED['cd_possible_moves']
    if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        return GAME_PARAMETERS_LOADED['cd_possible_retreats']
    if advancement_season in [mapping.SeasonEnum.ADJUST_SEASON]:
        return GAME_PARAMETERS_LOADED['cd_possible_builds']

    # should not happen
    return False


DEADLINE_COL = None
COUNTDOWN_COL = None


def get_game_status():
    """ get_game__status """

    def input_explain_game_type_callback(ev):  # pylint: disable=invalid-name
        ev.preventDefault()
        game_type = GAME_PARAMETERS_LOADED['game_type']
        explanation = common.TYPE_GAME_EXPLAIN_CONV[game_type]
        alert(explanation)

    def input_explain_dl_callback(ev):  # pylint: disable=invalid-name
        """ input_explain_dl_callback """

        ev.preventDefault()
        if GAME_PARAMETERS_LOADED['force_wait'] == 1:
            alert("Pour ralentir la partie, l'arbitre a neutralisé le bouton 'résoudre maintenant'")
        if GAME_PARAMETERS_LOADED['force_wait'] == -1:
            alert("Pour accélérer la partie, l'arbitre a neutralisé le bouton 'résoudre à la date limite'")

    def show_dc_callback(ev, allowed):  # pylint: disable=invalid-name
        """ show_variant_callback """

        ev.preventDefault()
        if allowed:
            alert("Pour cette phase de jeu, un désordre civil est possible. Cela signifie qu'un joueur en retard se voir sanctionné par des ordres de désordre civil (tenir en place, ne pas retraiter, ne pas construire, suppression par défaut)")
        else:
            alert("Pour cette phase de jeu, pas de désordre civil possible.")

    def show_variant_callback(ev, variant_name):  # pylint: disable=invalid-name
        """ show_variant_callback """

        ev.preventDefault()

        arrival = 'variant'

        # so that will go to proper page
        variants.set_arrival(arrival, variant_name)

        # action of going to game page
        PANEL_MIDDLE.clear()
        variants.render(PANEL_MIDDLE)

    def show_scoring_callback(ev, scoring_name):  # pylint: disable=invalid-name
        """ show_scoring_callback """

        ev.preventDefault()

        # so that will go to proper page
        ratings.set_arrival(scoring_name)

        # action of going to game page
        PANEL_MIDDLE.clear()
        ratings.render(PANEL_MIDDLE)

    def show_option_callback(ev):  # pylint: disable=invalid-name
        """ show_option_callback """

        ev.preventDefault()

        # so that will go to proper page
        technical.set_arrival('brouillard')

        # action of going to game page
        PANEL_MIDDLE.clear()
        technical.render(PANEL_MIDDLE)

    game_name = GAME_PARAMETERS_LOADED['name']
    game_description = GAME_PARAMETERS_LOADED['description']
    game_variant = GAME_PARAMETERS_LOADED['variant']
    game_fog = GAME_PARAMETERS_LOADED['fog']

    state_loaded = GAME_PARAMETERS_LOADED['current_state']
    for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
        if possible_state_desc == state_loaded:
            game_state_readable = possible_state_code
            break

    advancement_loaded = GAME_PARAMETERS_LOADED['current_advancement']
    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    game_season = common.get_full_season(advancement_loaded, VARIANT_DATA, nb_max_cycles_to_play, True)

    deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
    datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded)

    game_status_table = html.TABLE()

    row = html.TR()

    desc = html.DIV()
    desc <= "Partie "
    desc <= html.B(f"{game_name}")
    col = html.TD(desc)
    row <= col
    col = html.TD(f"id={GAME_ID}")
    row <= col

    # type of game
    form = html.FORM()
    game_type = GAME_PARAMETERS_LOADED['game_type']
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}
    game_type_name = game_type_conv[game_type]
    input_show_game_type = html.INPUT(type="submit", value=game_type_name, Class='btn-inside')
    input_show_game_type.attrs['style'] = 'font-size: 10px'
    input_show_game_type.bind("click", input_explain_game_type_callback)
    form <= input_show_game_type
    col = html.TD(form)
    row <= col

    # state
    col = html.TD(f"Etat {game_state_readable}")
    row <= col

    # season
    col = html.TD(f"Saison {game_season}")
    row <= col

    global DEADLINE_COL
    content = f"DL {datetime_deadline_loaded_str}"
    need_explanation = False

    if GAME_PARAMETERS_LOADED['soloed']:
        # keep value only for game master
        if ROLE_ID is None or ROLE_ID != 0:
            content = "(solo)"
    elif GAME_PARAMETERS_LOADED['end_voted']:
        # keep value only for game master
        if ROLE_ID is None or ROLE_ID != 0:
            content = "(fin votée)"
    elif GAME_PARAMETERS_LOADED['finished']:
        # keep value only for game master
        if ROLE_ID is None or ROLE_ID != 0:
            content = "(terminée)"

    # Display if forced to wait or now
    elif GAME_PARAMETERS_LOADED['force_wait'] == 1:
        content = html.B(f"= {content}")
        need_explanation = True
    elif GAME_PARAMETERS_LOADED['force_wait'] == -1:
        content = html.B(f"< {content}")
        need_explanation = True

    DEADLINE_COL = html.TD()
    DEADLINE_COL <= content
    if need_explanation:
        input_explain_dl = html.INPUT(type="submit", value="?", Class='btn-inside')
        input_explain_dl.attrs['style'] = 'font-size: 10px'
        input_explain_dl.bind("click", input_explain_dl_callback)
        DEADLINE_COL <= input_explain_dl

    row <= DEADLINE_COL

    global COUNTDOWN_COL
    COUNTDOWN_COL = html.TD("")
    row <= COUNTDOWN_COL

    # DC
    form = html.FORM()
    allowed = civil_disorder_allowed(advancement_loaded)
    game_dc = f"D.C. {'Oui' if allowed else 'Non'}"
    input_show_dc = html.INPUT(type="submit", value=game_dc, Class='btn-inside')
    input_show_dc.attrs['style'] = 'font-size: 10px'
    input_show_dc.bind("click", lambda e, v=allowed: show_dc_callback(e, v))
    if allowed:
        input_show_dc.attrs['style'] = 'color: red'
    form <= input_show_dc
    col = html.TD(form)
    row <= col

    # variant + link
    form = html.FORM()
    input_show_variant = html.INPUT(type="submit", value=game_variant, Class='btn-inside')
    input_show_variant.attrs['style'] = 'font-size: 10px'
    input_show_variant.bind("click", lambda e, v=game_variant: show_variant_callback(e, v))
    form <= input_show_variant
    col = html.TD(form)
    row <= col

    # option + link
    col = html.TD("")
    if game_fog:
        game_option_name = "Le brouillard"
        form = html.FORM()
        input_show_option = html.INPUT(type="submit", value=game_option_name, Class='btn-inside')
        input_show_option.attrs['style'] = 'font-size: 10px'
        input_show_option.bind("click", show_option_callback)
        form <= input_show_option
        col = html.TD(form)
    row <= col

    # scoring + link
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    game_scoring_name = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[game_scoring]
    form = html.FORM()
    input_show_scoring = html.INPUT(type="submit", value=game_scoring_name, Class='btn-inside')
    input_show_scoring.attrs['style'] = 'font-size: 10px'
    input_show_scoring.bind("click", lambda e, v=game_scoring: show_scoring_callback(e, v))
    form <= input_show_scoring
    col = html.TD(form)
    row <= col

    # game master
    if GAME_MASTER:
        col = html.TD(f"Arbitre {GAME_MASTER}")
    else:
        col = html.TD("(pas d'arbitre)")
    row <= col

    game_status_table <= row

    row = html.TR()

    next_previous_available = False
    if 'GAME_LIST' in storage:
        games_list = storage['GAME_LIST'].split(' ')
        if game_name in games_list:
            next_previous_available = True

    if next_previous_available:
        button_previous_game = html.BUTTON("partie précédente", Class='btn-inside')
        button_previous_game.style = {'font-size': '10px'}
        button_previous_game.bind("click", lambda e: play.next_previous_game(True))
    else:
        button_previous_game = html.BUTTON("partie précédente", disabled=True, Class='btn-inside')
        button_previous_game.style = {'pointer-events': 'none', 'font-size': '10px'}
    col = html.TD(button_previous_game)
    row <= col

    col = html.TD("<br>".join(game_description.split('\n')), colspan="10")
    row <= col

    if next_previous_available:
        button_next_game = html.BUTTON("partie suivante", Class='btn-inside')
        button_next_game.style = {'font-size': '10px'}
        button_next_game.bind("click", lambda e: play.next_previous_game(False))
    else:
        button_next_game = html.BUTTON("partie suivante", disabled=True, Class='btn-inside')
        button_next_game.style = {'pointer-events': 'none', 'font-size': '10px'}
    col = html.TD(button_next_game)
    row <= col

    game_status_table <= row

    # a few things need to be made clear

    # calculate it
    explanations = []

    if GAME_PARAMETERS_LOADED['nopress_current']:
        explanations.append("La presse (déclaration publique) est actuellement interdite")

    if GAME_PARAMETERS_LOADED['nomessage_current']:
        explanations.append("La messagerie (négociations privées entre joueurs) est actuellement interdite")

    if GAME_PARAMETERS_LOADED['game_type'] == 3:
        explanations.append("Attention Partie Blitz ouverte : la presse est autorisée mais HORS-JEU")

    # display it
    if explanations:
        row = html.TR()
        specific_information = html.DIV(Class='important')
        specific_information <= "Communication sur la partie : "
        for num, explanations in enumerate(explanations):
            specific_information <= f"{num + 1}) {explanations} "
        col = html.TD(specific_information, colspan="12")
        row <= col
        game_status_table <= row

    if GAME_PARAMETERS_LOADED['fast']:
        row = html.TR()
        specific_information = html.DIV("Partie en direct : utiliser le bouton 'recharger la partie' du menu 'Consulter' en attendant la résolution (puis retourner aux ordres)", Class='important')
        col = html.TD(specific_information, colspan="12")
        row <= col
        game_status_table <= row

    if GAME_PARAMETERS_LOADED['fog']:
        row = html.TR()
        specific_information = html.DIV("Partie brouillard : Pour soutenir offensivement ou convoyer une unité non vue, utiliser l'interface 'Imaginer'", Class='important')
        col = html.TD(specific_information, colspan="12")
        row <= col
        game_status_table <= row

    return game_status_table


def get_game_status_histo(variant_data, advancement_selected):
    """ get_game_status_histo """

    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    game_season = common.get_full_season(advancement_selected, variant_data, nb_max_cycles_to_play, False)

    game_status_table = html.TABLE()
    row = html.TR()
    col = html.TD(f"Saison {game_season}")
    row <= col
    game_status_table <= row

    return game_status_table


def game_orders_reload(game_id):
    """ game_orders_reload """

    orders_loaded = {}

    def reply_callback(req):
        nonlocal orders_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des ordres de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des ordres de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        orders_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return orders_loaded


def game_communication_orders_reload(game_id):
    """ game_communication_orders_reload """

    orders_loaded = None

    def reply_callback(req):
        nonlocal orders_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des ordres de communication la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des ordres de communication la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        orders_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-communication-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return orders_loaded


def show_board(panel):
    """ map and ratings """

    orders_data = None

    def callback_render(_):
        """ callback_render """

        # since orders are not involved not save/restore context

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the position and neutral centers
        POSITION_DATA.render(ctx)

        # put the legends
        VARIANT_DATA.render(ctx)

        # the orders if applicable
        if orders_data:
            orders_data.render(ctx)

    if ROLE_ID != 0:

        # load orders
        orders_loaded = game_orders_reload(GAME_ID)

        # digest the orders
        orders_data = mapping.Orders(orders_loaded, POSITION_DATA, [])

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    panel <= canvas
    panel <= html.BR()

    # ratings
    fog_of_war = GAME_PARAMETERS_LOADED['fog']
    game_over = GAME_PARAMETERS_LOADED['soloed'] or GAME_PARAMETERS_LOADED['end_voted'] or GAME_PARAMETERS_LOADED['finished']
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = common.make_rating_colours_window(fog_of_war, game_over, VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN, game_scoring, ROLE_ID, GAME_PLAYERS_DICT, ID2PSEUDO)
    panel <= rating_colours_window
    panel <= html.BR()


def game_fog_of_war_report_reload(game_id, role_id):
    """ game_fog_of_war_report_reload """

    report_loaded = {}

    def reply_callback(req):
        nonlocal report_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du rapport de résolution (brouillard) de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du rapport de résolution (brouillard) de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        report_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-fog-of-war-reports/{game_id}/{role_id}"

    # getting variant : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return report_loaded


def game_report_reload(game_id):
    """ game_report_reload """

    report_loaded = {}

    def reply_callback(req):
        nonlocal report_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du rapport de résolution de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du rapport de résolution de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        report_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-reports/{game_id}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return report_loaded


def game_incidents_reload(game_id):
    """ game_incidents_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents retards de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents retards de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_master_incidents_reload(game_id):
    """ game_master_incidents_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents retards de la partie pour l'arbitre : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents retards de la partie  pour l'arbitre : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-master-incidents/{game_id}"

    # extracting incidents from a game for master : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_incidents2_reload(game_id):
    """ game_incidents2_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents désordres civils  de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents désordres civils de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents2/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION


MY_SUB_PANEL = html.DIV(id="page")
MY_PANEL <= MY_SUB_PANEL
