""" variants """

# pylint: disable=pointless-statement, expression-not-assigned
from math import sqrt
from json import loads, dumps

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import mapping
import interface
import sandbox
import index
import memoize
import ezml_render


OPTIONS = {'Généralités': "Généralités sur les variantes implémentées sur le site"}
OPTIONS.update({f"{variant_name} ({nb_players}j.)": f"La variante {variant_name}" for variant_name, nb_players in config.VARIANT_NAMES_DICT.items()})
OPTIONS.update({'Fréquentation des variantes': "Statistiques sur la fréquentation des variantes sur le site"})
OPTIONS.update({'Equilibre des variantes': "Statistiques l'équilibre des variantes sur le site"})

ARRIVAL = None

# from home
VARIANT_REQUESTED_NAME = None

# from game
VARIANT_NAME = None

# this will come from variant
INTERFACE_CHOSEN = None
VARIANT_DATA = None
POSITION_DATA = None
ORDERS_DATA = None


def set_arrival(arrival, variant_requested_name=None):
    """ set_arrival """

    global ARRIVAL
    global VARIANT_REQUESTED_NAME

    ARRIVAL = arrival

    if variant_requested_name:
        VARIANT_REQUESTED_NAME = variant_requested_name


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


def create_initial_position():
    """ create_initial_position """

    global INTERFACE_CHOSEN
    global VARIANT_DATA
    global POSITION_DATA
    global ORDERS_DATA

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(VARIANT_NAME)
    if not variant_content_loaded:
        return

    # selected interface (user choice)
    INTERFACE_CHOSEN = interface.get_interface_from_variant(VARIANT_NAME)

    # from display chose get display parameters
    parameters_read = common.read_parameters(VARIANT_NAME, INTERFACE_CHOSEN)

    # build variant data
    VARIANT_DATA = mapping.Variant(VARIANT_NAME, variant_content_loaded, parameters_read)

    dict_made_units = {}
    dict_made_ownerships = {}

    # ownerships
    for role in VARIANT_DATA.roles.values():
        for start_center in role.start_centers:
            center_num = start_center.identifier
            role_num = role.identifier
            dict_made_ownerships[center_num] = role_num

    # units
    for role, role_start_units in VARIANT_DATA.start_units.items():
        role_num = role.identifier
        if role_num not in dict_made_units:
            dict_made_units[role_num] = []
        for (type_num, zone) in role_start_units:
            zone_num = zone.identifier
            dict_made_units[role_num].append([type_num, zone_num])

    # get the position
    position_loaded = {'ownerships': dict_made_ownerships, 'units': dict_made_units, 'forbiddens': {}, 'dislodged_ones': {}}

    # digest the position
    POSITION_DATA = mapping.Position(position_loaded, VARIANT_DATA)

    # get the orders from server (actually no)
    orders_loaded = {'fake_units': {}, 'orders': {}}

    # digest the orders
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA, [])


def show_variant():
    """ show_variant """

    global VARIANT_NAME
    global VARIANT_REQUESTED_NAME

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.set_arrival("variant", VARIANT_NAME)

        # action on importing game
        sandbox.import_position(POSITION_DATA)

        # action of going to sandbox page
        index.load_option(None, 'Bac à sable')

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

    def copy_url_show_callback(_):
        """ copy_url_show_callback """
        input_copy_url_show.select()
        # ev.setSelectionRange(0, 99999) # For mobile devices
        window.navigator.clipboard.writeText(input_copy_url_show.value)
        alert(f"Lien '{input_copy_url_show.value}' copié dans le presse papier...")

    # you get variant from game except if coming from home page

    # make sure we have a variant name
    if VARIANT_REQUESTED_NAME:
        VARIANT_NAME = VARIANT_REQUESTED_NAME
        VARIANT_REQUESTED_NAME = None
    else:
        if 'GAME_VARIANT' in storage:
            VARIANT_NAME = storage['GAME_VARIANT']
        else:
            VARIANT_NAME = config.FORCED_VARIANT_NAME

    # create position
    create_initial_position()

    map_size = VARIANT_DATA.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # put background (this will call the callback that display the whole map)
    img = common.read_map(VARIANT_NAME, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    input_export_sandbox = html.INPUT(type="submit", value="Exporter la position vers le bac à sable", Class='btn-inside')
    input_export_sandbox.bind("click", callback_export_sandbox)
    buttons_right <= input_export_sandbox
    buttons_right <= html.BR()
    buttons_right <= html.BR()

    url = f"{config.SITE_ADDRESS}?variant={VARIANT_NAME}"
    input_copy_url_show = html.INPUT(type="text", value=url)
    button_copy_url_show = html.BUTTON("Copier le lien pour inviter un joueur à consulter cette variante.", Class='btn-inside')
    button_copy_url_show.bind("click", copy_url_show_callback)
    buttons_right <= button_copy_url_show

    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= html.H3(f"La variante {VARIANT_NAME}")

    MY_SUB_PANEL <= my_sub_panel2
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= common.make_rating_colours_window(False, False, VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN, None, None, None, None)
    MY_SUB_PANEL <= html.BR()

    ezml_file = f"./variants/{VARIANT_NAME}/{VARIANT_NAME}.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_variant_basics():
    """ show_variant_basics """

    ezml_file = "./variants/generalites.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_variants_frequentation_data():
    """ show_variants_frequentation_data """

    def extract_variant_frequentation_data():
        """ extract_variant_frequentation_data """

        data = None

        def reply_callback(req):

            nonlocal data

            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au calcul de la fréquentation des variantes : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au calcul de la fréquentation des variantes : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                return

            data = req_result

        json_dict = {
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/extract_variants_data"

        # extract_histo_tournament_data : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return data

    # get the variants frequentations
    variants_freq_dict = extract_variant_frequentation_data()
    if not variants_freq_dict:
        alert("Pas de variantes ou erreur chargement dictionnaire frequentation tournois")
        return

    variants_table = html.TABLE()

    fields = ['variant', 'nb_players', 'games', 'affluence']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'variant': "nom de la variante", 'nb_players': "nombre de joueurs de la variante", 'games': "nombre de parties en cours ou archivées", 'affluence': "nombre de joueurs la jouant ou l'ayant jouée"}[field]
        col = html.TD(field_fr)
        thead <= col
    variants_table <= thead

    for variant_name, data in sorted(variants_freq_dict.items(), key=lambda t: t[1]['affluence'], reverse=True):
        row = html.TR()
        for field in fields:

            data['variant'] = None
            value = data[field]

            if field == 'variant':
                value = variant_name

            col = html.TD(value)

            row <= col

        variants_table <= row

    MY_SUB_PANEL <= html.H3("La fréquentation des variantes du site")
    MY_SUB_PANEL <= variants_table


def show_variants_balance_data():
    """ show_variants_balance_data """

    def variant_position_reload(variant_name):
        """ variant_position_reload : returns empty dict on error """

        positions_loaded = {}

        def reply_callback(req):
            nonlocal positions_loaded
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au chargement des positions des parties de la variante : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au chargement des positions des parties de la variante : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            positions_loaded = req_result

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/variant-positions/{variant_name}"

        # getting game position : do not need a token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return positions_loaded

    alert("Attention le calcul est un peu long...")

    MY_SUB_PANEL <= html.H3("L'équilibre des variantes du site")

    MY_SUB_PANEL <= html.DIV("ATTENTION : Le lecteur avisé (ce message s'adresse aux autres) sait que la vérité d'une mesure statistique est proportionelle à la taille de l'échantillon, aussi il prendra du recul sur les valeurs avec peu ou très peu de parties !", Class='important')

    for variant_name_loaded in config.VARIANT_NAMES_DICT:

        # for fast testing
        # if variant_name_loaded != 'hundred': continue

        # build dict of positions
        positions_dict_loaded = variant_position_reload(variant_name_loaded)
        if not positions_dict_loaded:
            alert("Erreur chargement positions des parties du tournoi")
            return

        # from variant name get variant content
        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                alert("Erreur chargement données variante de la partie")
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected display (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        if (variant_name_loaded, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = variant_data

        sc_table = {r: 0 for r in variant_data.roles if r}
        top_table = {r: 0 for r in variant_data.roles if r}
        solo_table = {r: 0 for r in variant_data.roles if r}
        elimination_table = {r: 0 for r in variant_data.roles if r}
        worst_centers_table = {r: 100000 for r in variant_data.roles if r}
        best_centers_table = {r: 0 for r in variant_data.roles if r}
        best_performance_table = {r: ((-100000, -100000, 0), None) for r in variant_data.roles if r}
        for game_id_str, data in positions_dict_loaded.items():
            game_score_table = {}
            for power in sc_table:
                game_score_table[power] = len([p for p in data['ownerships'].values() if int(p) == power])
            for power in sc_table:
                nb_centers = game_score_table[power]
                sc_table[power] += nb_centers
                if nb_centers < worst_centers_table[power]:
                    worst_centers_table[power] = nb_centers
                if nb_centers > best_centers_table[power]:
                    best_centers_table[power] = nb_centers
                if game_score_table[power] == max(game_score_table.values()):
                    top_table[power] += 1
                if game_score_table[power] > variant_data.number_centers() // 2:
                    solo_table[power] += 1
                if game_score_table[power] == 0:
                    elimination_table[power] += 1
                # performance is (- nb powers with more centers, - nb powers with same number of centers, nb centers)
                performance = (
                    - len([p for p, c in game_score_table.items() if c > nb_centers]),
                    - len([p for p, c in game_score_table.items() if c == nb_centers]),
                    game_score_table[power])
                if performance > best_performance_table[power][0]:
                    # we have better, we take slot
                    best_performance_table[power] = (performance, int(game_id_str))
                elif performance == best_performance_table[power][0]:
                    # we have same we cancel
                    best_performance_table[power] = (best_performance_table[power][0], None)

        variant_powers_results_table = html.TABLE()

        fields = ['flag', 'power', 'centers', 'worst', 'best', 'victories', 'solos', 'eliminations']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'flag': 'drapeau', 'power': 'puissance', 'centers': 'moyenne centres (possibles)', 'worst': 'pire', 'best': 'mieux', 'victories': 'victoires', 'solos': 'solos', 'eliminations': 'éliminations'}[field]
            col = html.TD(field_fr)
            thead <= col
        variant_powers_results_table <= thead

        nb_possible_centers = len(variant_data.centers)
        nb_games = len(positions_dict_loaded)

        for role_id in sorted(variant_data.roles, key=lambda r: variant_data.role_name_table[variant_data.roles[r]]):

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = variant_data.roles[role_id]
            role_name = variant_data.role_name_table[role]

            # flag
            col = html.TD()
            role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # average centers
            col = html.TD()
            value = sc_table[role_id] / nb_games
            col <= f"{value:.2f} ({nb_possible_centers})"
            row <= col

            # worst
            col = html.TD()
            value = worst_centers_table[role_id]
            col <= value
            row <= col

            # best
            col = html.TD()
            value = best_centers_table[role_id]
            col <= value
            row <= col

            # percent victories
            col = html.TD()
            value = (top_table[role_id] / nb_games) * 100
            col <= f"{value:.2f} %"
            row <= col

            # percent solos
            col = html.TD()
            value = (solo_table[role_id] / nb_games) * 100
            col <= f"{value:.2f} %"
            row <= col

            # percent eliminations
            col = html.TD()
            value = (elimination_table[role_id] / nb_games) * 100
            col <= f"{value:.2f} %"
            row <= col

            variant_powers_results_table <= row

        # standard deviation
        avg = sum(sc_table[ri] / nb_games for ri in variant_data.roles if ri != 0) / len([r for r in variant_data.roles if r])
        std_dev = sqrt(sum(((sc_table[ri] / nb_games) - avg) ** 2 for ri in variant_data.roles if ri != 0) / len([r for r in variant_data.roles if r]))
        deviation = (std_dev / nb_possible_centers) * 100

        # title
        MY_SUB_PANEL <= html.H4(variant_name_loaded)
        MY_SUB_PANEL <= variant_powers_results_table
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= f"Moyenne des centres : {avg:.2f} écart type : {std_dev:.2f} ... nombre de centres : {nb_possible_centers} donc déviation de {deviation:.2f} % (sur un échantillon de {nb_games} parties)"


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.UL()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top; padding: 0;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id='page')
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    global VARIANT_REQUESTED_NAME

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Généralités':
        show_variant_basics()
    elif item_name == 'Fréquentation des variantes':
        show_variants_frequentation_data()
    elif item_name == 'Equilibre des variantes':
        show_variants_balance_data()
    else:
        # remove the number of players on the right
        variant, _, __ = item_name.partition(' ')
        VARIANT_REQUESTED_NAME = variant
        show_variant()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    global ARRIVAL

    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # this means user wants to see variant
    if ARRIVAL == 'variant':
        ITEM_NAME_SELECTED = VARIANT_REQUESTED_NAME

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
