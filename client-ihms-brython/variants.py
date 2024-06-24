""" variants """

# pylint: disable=pointless-statement, expression-not-assigned
from json import loads, dumps

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import mapping
import interface
import sandbox
import index
import ezml_render

OPTIONS = {variant_name: f"La variante {variant_name} ({nb_players}j.)" for variant_name, nb_players in config.VARIANT_NAMES_DICT.items()}
OPTIONS.update({'Fréquentation des variantes': "Statistiques de fréquentation des variantes sur le site"})

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


def make_rating_colours_window(variant_data, position_data, interface_):
    """ make_rating_window """

    ratings = position_data.role_ratings()
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
    for role_name in ratings:
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
    for role_name in ratings:
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
    for role, ncenters in ratings.items():
        nunits = units[role]
        col = html.TD()
        if nunits != ncenters:
            col <= f"{ncenters} ({nunits})"
        else:
            col <= f"{ncenters}"
        rating_centers_row <= col

    return rating_table


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
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA, False)


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

            # put the centers
            VARIANT_DATA.render(ctx)

            # put the position
            POSITION_DATA.render(ctx)

            # put the legends at the end
            VARIANT_DATA.render_legends(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

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
    img = common.read_image(VARIANT_NAME, INTERFACE_CHOSEN)
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
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= html.H2(f"La variante {VARIANT_NAME}")
    MY_SUB_PANEL <= my_sub_panel2
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= make_rating_colours_window(VARIANT_DATA, POSITION_DATA, INTERFACE_CHOSEN)
    MY_SUB_PANEL <= html.BR()

    ezml_file = f"./variants/{VARIANT_NAME}/{VARIANT_NAME}.ezml"
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
        field_fr = {'variant': "nom de la variante", 'nb_players': "nombre de joueurs de la variante", 'games': "nombre de parties en cours ou terminées", 'affluence': "nombre de joueurs la jouant ou l'ayant jouée"}[field]
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


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
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

    if item_name == 'Fréquentation des variantes':
        show_variants_frequentation_data()
    else:
        VARIANT_REQUESTED_NAME = item_name
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
