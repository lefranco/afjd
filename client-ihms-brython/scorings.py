""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import mapping
import scoring
import interface
import ezml_render

OPTIONS = list(config.SCORING_CODE_TABLE.keys())

ARRIVAL = None

# from home
SCORING_REQUESTED = None


def set_arrival(arrival, scoring_requested=None):
    """ set_arrival """

    global ARRIVAL
    global SCORING_REQUESTED

    ARRIVAL = arrival

    if scoring_requested:
        SCORING_REQUESTED = scoring_requested


RATING_TABLE = {}


def show_scoring():
    """ show_scoring """

    def test_scoring_callback(ev, ratings_input):  # pylint: disable=invalid-name
        """ test_scoring_callback """

        ev.preventDefault()

        for name, element in ratings_input.items():
            val = 0
            try:
                val = int(element.value)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            RATING_TABLE[name] = val

        # scoring
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(SCORING_REQUESTED, solo_threshold, RATING_TABLE)

        score_desc = "\n".join([f"{k} : {v} points" for k, v in score_table.items()])
        alert(f"Dans cette configuration la marque est :\n{score_desc}")

        # back to where we started
        MY_SUB_PANEL.clear()
        show_scoring()

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = f"./scorings/{SCORING_REQUESTED}.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)

    title = html.H3("Tester !")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from display chose get display parameters
    interface_parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, interface_parameters_read)

    form = html.FORM()

    title_enter_centers = html.H4("Entrer les nombre de centres")
    form <= title_enter_centers

    ratings_input = {}
    for num, role in variant_data.roles.items():

        if num == 0:
            continue

        role_name = variant_data.role_name_table[role]

        fieldset = html.FIELDSET()
        legend_centers = html.LEGEND(role_name, title="nombre de centres")
        fieldset <= legend_centers
        input_centers = html.INPUT(type="number", value=str(RATING_TABLE[role_name]) if role_name in RATING_TABLE else "", Class='btn-inside')
        fieldset <= input_centers
        form <= fieldset

        ratings_input[role_name] = input_centers

    input_test_scoring = html.INPUT(type="submit", value="Calculer le scorage", Class='btn-inside')
    input_test_scoring.bind("click", lambda e, ri=ratings_input: test_scoring_callback(e, ri))
    form <= input_test_scoring

    MY_SUB_PANEL <= form


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id='page')
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    global SCORING_REQUESTED

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    SCORING_REQUESTED = config.SCORING_CODE_TABLE[item_name]
    show_scoring()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    global ARRIVAL

    ITEM_NAME_SELECTED = OPTIONS[0]

    # this means user wants to see variant
    if ARRIVAL == 'scoring':
        ITEM_NAME_SELECTED = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[SCORING_REQUESTED]

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
