""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common

OPTIONS = {
    'Rectifier paramètres': "Rectifier un des paramètres de la partie séléctionnée",
}

MAX_LEN_GAME_NAME = 50
MAX_LEN_VARIANT_NAME = 50

DEFAULT_SCORING_CODE = "CDIP"
DEFAULT_DEADLINE_TIME = 21
DEFAULT_GRACE_DURATION = 24
DEFAULT_SPEED_MOVES = 72
DEFAULT_SPEED_OTHERS = 24
DEFAULT_NB_CYCLES = 7


def information_about_input():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= "Survolez les titres pour pour plus de détails"
    return information


def rectify_parameters_game():
    """ rectify_parameters_game """

    # declare the values
    anonymity_loaded = None
    access_nopress_loaded = None
    access_nomessage_loaded = None
    description_loaded = None
    scoring_code_loaded = None
    access_restriction_reliability_loaded = None
    access_restriction_regularity_loaded = None
    access_restriction_performance_loaded = None
    deadline_hour_loaded = None
    deadline_sync_loaded = None
    grace_duration_loaded = None
    speed_moves_loaded = None
    cd_possible_moves_loaded = None
    speed_retreats_loaded = None
    cd_possible_retreats_loaded = None
    speed_adjustments_loaded = None
    cd_possible_builds_loaded = None
    play_weekend_loaded = None


    information_displayed_disorder = False

    def display_disorder_callback(_):
        """ display_disorder_callback """

        nonlocal information_displayed_disorder

        if input_cd_possible_moves.checked or input_cd_possible_retreats.checked or input_cd_possible_builds.checked:
            if not information_displayed_disorder:
                alert("Attention : autoriser le Désordre Civil sur une partie (quelque soit la saison) lui enlève automatiquement l'éligibilité pour le calcul du ELO")
                information_displayed_disorder = True

    def rectify_parameters_reload():
        """ rectify_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status

            nonlocal anonymity_loaded
            nonlocal access_nopress_loaded
            nonlocal access_nomessage_loaded
            nonlocal description_loaded
            nonlocal scoring_code_loaded
            nonlocal access_restriction_reliability_loaded
            nonlocal access_restriction_regularity_loaded
            nonlocal access_restriction_performance_loaded
            nonlocal deadline_hour_loaded
            nonlocal deadline_sync_loaded
            nonlocal grace_duration_loaded
            nonlocal speed_moves_loaded
            nonlocal cd_possible_moves_loaded
            nonlocal speed_retreats_loaded
            nonlocal cd_possible_retreats_loaded
            nonlocal speed_adjustments_loaded
            nonlocal cd_possible_builds_loaded
            nonlocal play_weekend_loaded

            req_result = loads(req.text)

            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération anonymat de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération anonymat de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            anonymity_loaded = req_result['anonymous']
            access_nopress_loaded = req_result['nopress_current']
            access_nomessage_loaded = req_result['nomessage_current']
            description_loaded = req_result['description']
            scoring_code_loaded = req_result['scoring']
            access_restriction_reliability_loaded = req_result['access_restriction_reliability']
            access_restriction_regularity_loaded = req_result['access_restriction_regularity']
            access_restriction_performance_loaded = req_result['access_restriction_performance']
            deadline_hour_loaded = req_result['deadline_hour']
            deadline_sync_loaded = req_result['deadline_sync']
            grace_duration_loaded = req_result['grace_duration']
            speed_moves_loaded = req_result['speed_moves']
            cd_possible_moves_loaded = req_result['cd_possible_moves']
            speed_retreats_loaded = req_result['speed_retreats']
            cd_possible_retreats_loaded = req_result['cd_possible_retreats']
            speed_adjustments_loaded = req_result['speed_adjustments']
            cd_possible_builds_loaded = req_result['cd_possible_builds']
            play_weekend_loaded = req_result['play_weekend']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_anonymity_games_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification anonymat de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification anonymat de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"L'accès à l'anonymat a été modifié : {messages}")

        ev.preventDefault()

        json_dict = {
            'name': game,
            'anonymous': input_anonymous.checked,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game anonimity : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    def change_access_messages_games_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification acces messagerie de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification acces messagerie de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"L'accès à la messagerie a été modifié : {messages}")

        ev.preventDefault()

        json_dict = {
            'name': game,
            'nopress_current': input_nopress.checked,
            'nomessage_current': input_nomessage.checked,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    def change_description_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la description de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la description de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La description a été modifiée : {messages}")

        ev.preventDefault()

        description = input_description.value

        json_dict = {
            'name': game,
            'description': description,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game description : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    def change_scoring_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du scorage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du scorage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le scorage a été modifié : {messages}")

        ev.preventDefault()

        scoring = config.SCORING_CODE_TABLE[input_scoring.value]

        json_dict = {
            'name': game,
            'scoring': scoring,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    def change_access_parameters_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du paramètre d'accès à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du paramètre d'accès à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Les paramètres d'accès ont été modifiés : {messages}")

        ev.preventDefault()

        access_restriction_reliability = input_access_restriction_reliability.value
        access_restriction_regularity = input_access_restriction_regularity.value
        access_restriction_performance = input_access_restriction_performance.value

        json_dict = {
            'name': game,
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game access parameters : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    def change_pace_parameters_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du rythme à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du rythme à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Les paramètres de cadence ont été modifiés : {messages}")

        ev.preventDefault()

        try:
            deadline_hour = int(input_deadline_hour.value)
        except:  # noqa: E722 pylint: disable=bare-except
            deadline_hour = None

        deadline_sync = int(input_deadline_sync.checked)

        try:
            grace_duration = int(input_grace_duration.value)
        except:  # noqa: E722 pylint: disable=bare-except
            grace_duration = None

        try:
            speed_moves = int(input_speed_moves.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_moves = None

        cd_possible_moves = int(input_cd_possible_moves.checked)

        try:
            speed_retreats = int(input_speed_retreats.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_retreats = None

        cd_possible_retreats = int(input_cd_possible_retreats.checked)

        try:
            speed_adjustments = int(input_speed_adjustments.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_adjustments = None

        cd_possible_builds = int(input_cd_possible_builds.checked)
        play_weekend = int(input_play_weekend.checked)

        json_dict = {
            'name': game,
            'deadline_hour': deadline_hour,
            'deadline_sync': deadline_sync,
            'grace_duration': grace_duration,
            'speed_moves': speed_moves,
            'cd_possible_moves': cd_possible_moves,
            'speed_retreats': speed_retreats,
            'cd_possible_retreats': cd_possible_retreats,
            'speed_adjustments': speed_adjustments,
            'cd_possible_builds': cd_possible_builds,
            'play_weekend': play_weekend,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game pace parameters : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters_game()

    MY_SUB_PANEL <= html.H3("Rectification de paramètres de la partie")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    status = rectify_parameters_reload()
    if not status:
        return

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Anonymat")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_anonymous = html.LEGEND("anonyme", title="Les identités des joueurs ne sont pas révélées avant la fin de la partie")
    fieldset <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=anonymity_loaded, Class='btn-inside')
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_change_anonymity_game = html.INPUT(type="submit", value="Changer l'anonymat de la partie", Class='btn-inside')
    input_change_anonymity_game.bind("click", change_anonymity_games_callback)
    form <= input_change_anonymity_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Accès aux messagerie")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nopress = html.LEGEND("pas de déclaration", title="Les joueurs ne peuvent pas communiquer (déclarer) par message *public* avant la fin de la partie")
    fieldset <= legend_nopress
    input_nopress = html.INPUT(type="checkbox", checked=access_nopress_loaded, Class='btn-inside')
    fieldset <= input_nopress
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nomessage = html.LEGEND("pas de négociation", title="Les joueurs ne peuvent pas communiquer (négocier) par message *privé* avant la fin de la partie")
    fieldset <= legend_nomessage
    input_nomessage = html.INPUT(type="checkbox", checked=access_nomessage_loaded, Class='btn-inside')
    fieldset <= input_nomessage
    form <= fieldset

    form <= html.BR()

    input_change_message_game = html.INPUT(type="submit", value="Changer l'accès aux déclarations et négociations de la partie", Class='btn-inside')
    input_change_message_game.bind("click", change_access_messages_games_callback)
    form <= input_change_message_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Description")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Cela peut être long. Exemple : 'une partie entre étudiants de l'ETIAM'")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=8, cols=80)
    input_description <= description_loaded
    fieldset <= input_description
    form <= fieldset

    form <= html.BR()

    input_change_description_game = html.INPUT(type="submit", value="Changer la description de la partie", Class='btn-inside')
    input_change_description_game.bind("click", change_description_game_callback)
    form <= input_change_description_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Scorage")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="La méthode pour compter les points (applicable aux parties en tournoi uniquement)")
    fieldset <= legend_scoring
    input_scoring = html.SELECT(type="select-one", value="", Class='btn-inside')

    for scoring_name in config.SCORING_CODE_TABLE:
        option = html.OPTION(scoring_name)
        if config.SCORING_CODE_TABLE[scoring_name] == scoring_code_loaded:
            option.selected = True
        input_scoring <= option

    fieldset <= input_scoring
    form <= fieldset

    form <= html.BR()

    input_change_scoring_game = html.INPUT(type="submit", value="Changer le scorage de la partie", Class='btn-inside')
    input_change_scoring_game.bind("click", change_scoring_game_callback)
    form <= input_change_scoring_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Paramètres d'accès")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    fieldset <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability_loaded, Class='btn-inside')
    fieldset <= input_access_restriction_reliability
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    fieldset <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity_loaded, Class='btn-inside')
    fieldset <= input_access_restriction_regularity
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    fieldset <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance_loaded, Class='btn-inside')
    fieldset <= input_access_restriction_performance
    form <= fieldset

    form <= html.BR()

    input_change_access_game = html.INPUT(type="submit", value="Changer les paramètres d'accès à la partie", Class='btn-inside')
    input_change_access_game.bind("click", change_access_parameters_game_callback)
    form <= input_change_access_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Paramètres de cadence")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    # deadline related

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("heure de date limite", title="Heure GMT de la journée à laquelle placer les dates limites")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="number", value=deadline_hour_loaded, Class='btn-inside')
    fieldset <= input_deadline_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_sync = html.LEGEND("synchronisation des date limites", title="Faut-il synchroniser les dates limites à une heure donnée")
    fieldset <= legend_deadline_sync
    input_deadline_sync = html.INPUT(type="checkbox", checked=deadline_sync_loaded, Class='btn-inside')
    fieldset <= input_deadline_sync
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_grace_duration = html.LEGEND("durée de grâce", title="Nombre d'heures (minutes pour une partie en direct) alloués avant fin de la grâce")
    fieldset <= legend_grace_duration
    input_grace_duration = html.INPUT(type="number", value=grace_duration_loaded, Class='btn-inside')
    fieldset <= input_grace_duration
    form <= fieldset

    # moves

    fieldset = html.FIELDSET()
    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de mouvements")
    fieldset <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves_loaded, Class='btn-inside')
    fieldset <= input_speed_moves
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    fieldset <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=cd_possible_moves_loaded, Class='btn-inside')
    input_cd_possible_moves.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_moves
    form <= fieldset

    # retreats

    fieldset = html.FIELDSET()
    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de retraites")
    fieldset <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats_loaded, Class='btn-inside')
    fieldset <= input_speed_retreats
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    fieldset <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=cd_possible_retreats_loaded, Class='btn-inside')
    input_cd_possible_retreats.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_retreats
    form <= fieldset

    # adjustments

    fieldset = html.FIELDSET()
    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite d'ajustements")
    fieldset <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments_loaded, Class='btn-inside')
    fieldset <= input_speed_adjustments
    form <= fieldset

    # builds/removals

    fieldset = html.FIELDSET()
    legend_cd_possible_builds = html.LEGEND("DC possible ajustements", title="Désordre civil possible pour une résolution d'ajustements")
    fieldset <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=cd_possible_builds_loaded, Class='btn-inside')
    input_cd_possible_builds.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_builds
    form <= fieldset

    # ---

    fieldset = html.FIELDSET()
    legend_play_weekend = html.LEGEND("jeu weekend", title="La date limite peut elle se trouver en fin de semaine")
    fieldset <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=play_weekend_loaded, Class='btn-inside')
    fieldset <= input_play_weekend
    form <= fieldset

    form <= html.BR()

    input_change_pace_game = html.INPUT(type="submit", value="Changer le rythme de la partie", Class='btn-inside')
    input_change_pace_game.bind("click", change_pace_parameters_game_callback)
    form <= input_change_pace_game

    MY_SUB_PANEL <= form


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


ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]


def load_option(_, item_name):
    """ load_option """

    global ITEM_NAME_SELECTED

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Rectifier paramètres':
        rectify_parameters_game()

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

    global ITEM_NAME_SELECTED

    if 'GAME' in storage:
        ITEM_NAME_SELECTED = 'Changer état'
    else:
        ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # always back to top
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
