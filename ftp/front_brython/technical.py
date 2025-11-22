""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import document, html, alert, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import interface
import whynot
import mydialog
import memoize
import ezml_render
import common
import mapping
import allgames
import play


OPTIONS = {
    'Documents': "Lien vers différents documents techniques sur le jeu",
    'Pourquoi yapa': "Complément à la Foire Aux Questions du site",
    'Choix d\'interface': "Choisir une interface différente de celle par défaut pour voir les parties",
    'Calcul du ELO': "Détail de la méthode de calcul du E.L.O. utilisé sur le site",
    'Le brouillard de guerre': "Spécifications du  brouillard de guerre pour une partie",
    'Ordres de com\'': "Explications sur les ordres de communication",
    'Utilisations ordres de com\'': "Toutes les utilisations des ordres de communication",
    'Fuseaux horaires': "Des informations les fuseaux horaires dans le monde",
    'Langage Markup Facile': "Des informations sur un langage de construction facile de pages HTML pour les descriptions techniques",
    'Evolution de la fréquentation': "Evolution sous forme graphique du nombre de joueurs actifs sur le site"
}


ARRIVAL = None

# from home
OPTION_REQUESTED = None


def set_arrival(arrival):
    """ set_arrival """

    global ARRIVAL

    ARRIVAL = arrival


def get_all_games_communications_orders():
    """ get_all_games_communications_orders : returns empty dict if problem """

    dict_communication_orders_data = {}

    def reply_callback(req):
        nonlocal dict_communication_orders_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des ordres de communication pour toutes les parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des ordres de communication pour toutes les parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_communication_orders_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/extract_com_orders_data"

    # get roles that submitted orders : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_communication_orders_data


def show_technical():
    """ show_technical """

    MY_SUB_PANEL <= html.H3("Recueil de documents techniques")

    title1 = html.H3("Règles du jeu officielles")
    MY_SUB_PANEL <= title1

    link1 = html.A(href="./docs/DiplomacyRGS_Rulebook_v6_LR.pdf", target="_blank")
    MY_SUB_PANEL <= link1
    link1 <= "Lien vers les règles officielles du jeu"

    # --

    title2 = html.H3("Algorithme de résolution (D.A.T.C.)")
    MY_SUB_PANEL <= title2

    link2 = html.A(href="./docs/DATC.html", target="_blank")
    link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
    MY_SUB_PANEL <= link2

    # --

    title3 = html.H3("Choix d'implémentation")
    MY_SUB_PANEL <= title3

    link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
    link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
    MY_SUB_PANEL <= link3

    # --

    title4 = html.H3("Création de variante")
    MY_SUB_PANEL <= title4

    link41 = html.A(href="./docs/Requis_Variantes.pdf", target="_blank")
    link41 <= "Comment créer les fichiers nécessaire pour une variante"
    MY_SUB_PANEL <= link41

    # --

    title5 = html.H3("Les sources du site")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="https://github.com/lefranco/afjd", target="_blank")
    link5 <= "Lien vers l'espace GITHUB qui archive tous les sources de la brique jeu (Diplomania v1 'front-end' et 'back-end')"
    MY_SUB_PANEL <= link5

    # --

    title7 = html.H3("Document d'interface de l'API")
    MY_SUB_PANEL <= title7

    link71 = html.A(href="https://afjdserveurressources.wordpress.com/", target="_blank")
    link71 <= "Si vous voulez vous aussi développer votre front end..."
    MY_SUB_PANEL <= link71

    # --

    title8 = html.H3("Remerciements")
    MY_SUB_PANEL <= title8

    link81 = html.A(href="https://brython.info/", target="_blank")
    link81 <= "Outil utilisé pour ce site web"
    MY_SUB_PANEL <= link81

    MY_SUB_PANEL <= html.P()

    link82 = html.A(href="https://www.flaticon.com/", target="_blank")
    link82 <= "Icônes utilisées pour ce site web"
    MY_SUB_PANEL <= link82


WHYNOT_DISPLAYED_TABLE = {k: False for k in whynot.WHYNOT_CONTENT_TABLE}
WHYNOT_CONTENT = html.DIV("faq")


def show_whynot():
    """ show_whynot """

    def reveal_callback(_, question):
        """ reveal_callback """

        WHYNOT_DISPLAYED_TABLE[question] = not WHYNOT_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_whynot()

    title1 = html.H3("Pourquoi c'est pas comme ça ?")
    MY_SUB_PANEL <= title1

    WHYNOT_CONTENT.clear()

    for question_txt, answer_txt in whynot.WHYNOT_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt, Class='btn-inside')
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        WHYNOT_CONTENT <= reveal_button

        if WHYNOT_DISPLAYED_TABLE[question_txt]:

            whynot_elt = html.DIV(answer_txt, Class='faq-info')
            WHYNOT_CONTENT <= whynot_elt

        WHYNOT_CONTENT <= html.P()

    MY_SUB_PANEL <= WHYNOT_CONTENT


def select_interface():
    """ select_interface """

    variant_name_loaded = None

    def select_interface_callback(_, user_interface):
        """ select_interface_callback """

        interface.set_interface(variant_name_loaded, user_interface)
        mydialog.info_go(f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}")

        # we do not go back to where we started
        # this is intended otherwise the new maps are not active
        alert("Interface sélectionnée, rechargement du site...")

    title1 = html.H3("Choix d'interface")
    MY_SUB_PANEL <= title1

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable (pour la variante)")
        return

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    information = html.DIV(Class='important')
    information <= "Une 'interface' vous permet d'avoir une carte et des trigrammes de désignation des régions spécifiques c'est-à-dire différents de ceux pratiqués sur le site"
    MY_SUB_PANEL <= information
    MY_SUB_PANEL <= html.BR()

    select_table = html.TABLE()

    for user_interface in interface.INTERFACE_TABLE[variant_name_loaded]:

        # get description
        with open(f"./variants/{variant_name_loaded}/{user_interface}/README", "r", encoding="utf-8") as file_ptr:
            lines = file_ptr.readlines()
        description = html.DIV(Class='note')
        for line in lines:
            description <= line
            description <= html.BR()

        form = html.FORM()
        fieldset = html.FIELDSET()
        legend_display = html.LEGEND(user_interface, title=description)
        fieldset <= legend_display
        form <= fieldset

        fieldset = html.FIELDSET()
        fieldset <= description
        form <= fieldset

        form <= html.BR()

        input_select_interface = html.INPUT(type="submit", value="Sélectionner cette interface", Class='btn-inside')
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    MY_SUB_PANEL <= select_table


def show_elo_calculation():
    """ show_elo_calculation """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/calcul_elo.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_fog_of_war():
    """ show_fog """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./options/brouillard/brouillard.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_com_orders():
    """ show_com_orders """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/communication_orders.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_com_orders_usages():
    """ show_com_orders_usages """

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        show_com_orders_usages()

    def show_season_callback(ev, game_name, game_data_sel, advancement):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        allgames.show_game_selected()

        play.set_arrival('position')
        play.set_arrival2(advancement)

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    overall_time_before = time()

    MY_SUB_PANEL <= html.H3("Toutes les utilisations des ordres de com'")

    games_dict = common.get_games_data(1, 3)  # ongoing, archived or distinguished
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    dict_missing_orders_data = get_all_games_communications_orders()
    if not dict_missing_orders_data:
        alert("Erreur chargement des ordres de com' dans les parties")
        return

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Mode liens externes (plus lent mais conserve cette page)", Class='btn-inside')
    else:
        button = html.BUTTON("Mode boutons (plus rapide mais remplace cette page)", Class='btn-inside')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    delays_table = html.TABLE()

    # the display order
    fields = ['name', 'advancements', 'variant', 'game_type', 'current_state']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'advancements': 'saisons à jouer', 'variant': 'variante', 'game_type': 'type de partie', 'current_state': 'état', }[field]
        col = html.TD(field_fr)
        thead <= col
    delays_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    # conversion
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

    # force sort according to deadline (latest games first of course)
    for game_id_str, data in sorted(games_dict.items(), key=lambda t: int(t[0]), reverse=True):

        if game_id_str not in dict_missing_orders_data:
            continue

        data['advancements'] = None

        # variant is available
        variant_name_loaded = data['variant']

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

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'advancements':
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = html.DIV()
                if storage['GAME_ACCESS_MODE'] == 'button':
                    for advancement_loaded in dict_missing_orders_data[game_id_str]:
                        season = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)
                        button = html.BUTTON(season, Class='btn-inside')
                        button.bind("click", lambda e, gn=game_name, gds=game_data_sel, ad=advancement_loaded: show_season_callback(e, gn, gds, ad))
                        value <= " "
                        value <= button
                else:
                    for advancement_loaded in dict_missing_orders_data[game_id_str]:
                        season = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)
                        link = html.A(season, href=f"?game={game_name}&arrival=position&advancement={advancement_loaded}", title="Cliquer pour aller dans la partie", target="_blank")
                        value <= " "
                        value <= link

            if field == 'game_type':
                explanation = common.TYPE_GAME_EXPLAIN_CONV[value]
                stats = game_type_conv[value]
                value = html.DIV(stats, title=explanation)

            if field == 'current_state':
                state_name = data[field]
                value = rev_state_code_table[state_name]

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        delays_table <= row

    MY_SUB_PANEL <= delays_table
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed:.2f} secs pour {sum(len(a) for a in dict_missing_orders_data.values())} occurences sur {len(dict_missing_orders_data)} parties."
    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def show_time_zones():
    """ show_time_zones """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/fuseaux_horaires.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_ezml_spec():
    """ show_ezml_spec """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/ezml_description.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def frequentation_evolution():
    """ frequentation_evolution """

    # load frequentation directly
    host = config.SERVER_CONFIG['FREQUENTATION']['HOST']
    port = config.SERVER_CONFIG['FREQUENTATION']['PORT']
    url = f"{host}:{port}/"

    # use button
    button = html.BUTTON("Lancement du calcul de fréquentation", id='frequentation_link', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open(url))
    document['frequentation_link'].click()


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

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Documents':
        show_technical()
    if item_name == 'Pourquoi yapa':
        show_whynot()
    if item_name == 'Choix d\'interface':
        select_interface()
    if item_name == 'Calcul du ELO':
        show_elo_calculation()
    if item_name == 'Le brouillard de guerre':
        show_fog_of_war()
    if item_name == 'Ordres de com\'':
        show_com_orders()
    if item_name == 'Utilisations ordres de com\'':
        show_com_orders_usages()
    if item_name == 'Fuseaux horaires':
        show_time_zones()
    if item_name == 'Langage Markup Facile':
        show_ezml_spec()
    if item_name == 'Evolution de la fréquentation':
        frequentation_evolution()

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


# starts here
PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    # always back to top
    global ITEM_NAME_SELECTED
    global ARRIVAL

    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # this means user wants to see option
    if ARRIVAL == 'brouillard':
        ITEM_NAME_SELECTED = 'Le brouillard de guerre'

    if ARRIVAL == 'communication':
        ITEM_NAME_SELECTED = 'Ordres de com\''

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
