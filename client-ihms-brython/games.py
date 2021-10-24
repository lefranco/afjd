""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

#  from browser.widgets.dialog import Dialog  # pylint: disable=import-error
#  from browser import bind  # pylint: disable=import-error


import config
import common
import selection

my_panel = html.DIV(id="games")

OPTIONS = ['créer', 'changer description', 'changer paramètres accès', 'changer date limite', 'changer paramètre cadence', 'changer état', 'supprimer']

MAX_LEN_NAME = 30

DEFAULT_VARIANT = 'standard'
DEFAULT_SPEED_MOVES = 2
DEFAULT_SPEED_OTHERS = 1
DEFAULT_CD_POSSIBLE_MOVES_BUILDS = 0
DEFAULT_CD_OTHERS = 1
DEFAULT_VICTORY_CENTERS = 18
DEFAULT_NB_CYCLES = 99


def information_about_game():
    """ information_about_account """

    information = html.DIV()
    information <= "Survolez les titres pour pour plus de détails"
    return information


def create_game():
    """ create_game """

    def create_game_callback(_):
        """ create_game_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La partie a été créé : {messages}", remove_after=config.REMOVE_AFTER)

        name = input_name.value

        if not name:
            alert("Nom manquant")
            return
        if len(name) > MAX_LEN_NAME:
            alert("Nom trop long")
            return

        variant = input_variant.value

        if not variant:
            alert("Variante manquante")
            return
        if len(variant) > MAX_LEN_NAME:
            alert("Variante trop longue")
            return

        archive = int(input_archive.checked)
        manual = int(input_manual.checked)
        anonymous = int(input_anonymous.checked)
        nomessage = int(input_nomessage.checked)
        nopress = int(input_nopress.checked)
        fast = int(input_fast.checked)

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
        cd_possible_removals = int(input_cd_possible_removals.checked)
        play_weekend = int(input_play_weekend.checked)

        try:
            access_code = int(input_access_code.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_code = None

        try:
            access_restriction_reliability = int(input_access_restriction_reliability.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_reliability = None

        try:
            access_restriction_regularity = int(input_access_restriction_regularity.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_regularity = None

        try:
            access_restriction_performance = int(input_access_restriction_performance.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_performance = None

        try:
            nb_max_cycles_to_play = int(input_nb_max_cycles_to_play.value)
        except:  # noqa: E722 pylint: disable=bare-except
            nb_max_cycles_to_play = None

        try:
            victory_centers = int(input_victory_centers.value)
        except:  # noqa: E722 pylint: disable=bare-except
            victory_centers = None

        # these are automatic
        time_stamp = time.time()
        time_creation = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        time_creation_str = datetime.datetime.strftime(time_creation, "%d-%m-%Y %H:%M:%S")
        description = f"game created at {time_creation_str} (gmt time) by {pseudo} variant {variant}"
        state = 0

        json_dict = {
            'name': name,
            'variant': variant,
            'archive': archive,
            'manual': manual,

            'anonymous': anonymous,
            'nomessage': nomessage,
            'nopress': nopress,
            'fast': fast,

            'speed_moves': speed_moves,
            'cd_possible_moves': cd_possible_moves,
            'speed_retreats': speed_retreats,
            'cd_possible_retreats': cd_possible_retreats,
            'speed_adjustments': speed_adjustments,
            'cd_possible_builds': cd_possible_builds,
            'cd_possible_removals': cd_possible_removals,
            'play_weekend': play_weekend,

            'access_code': access_code,
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,

            'nb_max_cycles_to_play': nb_max_cycles_to_play,
            'victory_centers': victory_centers,

            'description': description,
            'current_state': state,

            'pseudo': pseudo
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"

        # creating a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    form <= html.B("Vous voulez jouer ? Crééz-la partie et démissionez ensuite de l'arbitrage (appariement). Un arbitre sera alloué automatiquement...")
    form <= html.BR()
    form <= html.BR()

    form <= information_about_game()
    form <= html.BR()

    legend_title_main = html.LEGEND("Paramètres principaux de la partie - ne peuvent plus être changés la partie créée")
    legend_title_main.style = {
        'color': 'red',
    }
    form <= legend_title_main

    legend_name = html.LEGEND("nom")
    form <= legend_name
    input_name = html.INPUT(type="text", value="", title="Nom de la partie (faites court et simple)")
    form <= input_name
    form <= html.BR()

    legend_variant = html.LEGEND("variante", title="(imposée pour me moment)")
    form <= legend_variant
    input_variant = html.INPUT(type="select-one", readonly=True, value=DEFAULT_VARIANT)
    form <= input_variant
    form <= html.BR()

    legend_archive = html.LEGEND("archive", title="Partie pour les archives - la partie n'est pas jouée - l'arbitre passe tous les ordres")
    form <= legend_archive
    input_archive = html.INPUT(type="checkbox", checked=False)
    form <= input_archive
    form <= html.BR()

    legend_manual = html.LEGEND("casting manuel", title="L'arbitre attribue les rôles dans la partie et non le système")
    form <= legend_manual
    input_manual = html.INPUT(type="checkbox", checked=False)
    form <= input_manual
    form <= html.BR()

    legend_title_terms = html.LEGEND("Modalités de la partie - ne peuvent plus être changés la partie créée")
    legend_title_terms.style = {
        'color': 'red',
    }
    form <= legend_title_terms

    legend_anonymous = html.LEGEND("anonyme", title="Les identités des joueurs ne sont pas révélées avant la fin de la partie")
    form <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=False)
    form <= input_anonymous
    form <= html.BR()

    legend_nomessage = html.LEGEND("pas de message", title="Les joueurs ne peuvent pas communiquer par message avant la fin de la partie")
    form <= legend_nomessage
    input_nomessage = html.INPUT(type="checkbox", checked=False)
    form <= input_nomessage
    form <= html.BR()

    legend_nopress = html.LEGEND("pas de presse", title="Les joueurs ne peuvent pas communiquer par presse avant la fin de la partie")
    form <= legend_nopress
    input_nopress = html.INPUT(type="checkbox", checked=False)
    form <= input_nopress
    form <= html.BR()

    legend_fast = html.LEGEND("rapide", title="Les résolutions se font aussi que possible, le système n'ajoute pas les jours aux dates limites")
    form <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=False)
    form <= input_fast
    form <= html.BR()

    legend_title_pace = html.LEGEND("Cadence de la partie")
    legend_title_pace.style = {
        'color': 'red',
    }
    form <= legend_title_pace

    # moves

    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre de jours alloués avant la date limite de mouvements")
    form <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=DEFAULT_SPEED_MOVES)
    form <= input_speed_moves
    form <= html.BR()

    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    form <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_moves
    form <= html.BR()

    # retreats

    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre de jours alloués avant la date limite de retraites")
    form <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=DEFAULT_SPEED_OTHERS)
    form <= input_speed_retreats
    form <= html.BR()

    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    form <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=True)
    form <= input_cd_possible_retreats
    form <= html.BR()

    # adjustments

    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre de jours alloués avant la date limite d'ajustements")
    form <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=DEFAULT_SPEED_OTHERS)
    form <= input_speed_adjustments
    form <= html.BR()

    # builds

    legend_cd_possible_builds = html.LEGEND("DC possible constructions", title="Désordre civil possible pour une résolution d'ajustements - constructions")
    form <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_builds
    form <= html.BR()

    # removals

    legend_cd_possible_removals = html.LEGEND("DC possible suppressions", title="Désordre civil possible pour une résolution d'ajustements - suppressions")
    form <= legend_cd_possible_removals
    input_cd_possible_removals = html.INPUT(type="checkbox", checked=True)
    form <= input_cd_possible_removals
    form <= html.BR()

    # ---

    legend_play_weekend = html.LEGEND("jeu weekend", title="La date limite peut elle se trouver en fin de semaine")
    form <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=True)
    form <= input_play_weekend
    form <= html.BR()

    legend_title_access = html.LEGEND("Accès à la partie - ne peuvent plus être changés la partie démarrée")
    legend_title_access.style = {
        'color': 'red',
    }
    form <= legend_title_access

    legend_access_code = html.LEGEND("code accès", title="Code d'accès à la partie")
    form <= legend_access_code
    input_access_code = html.INPUT(type="number", value="")
    form <= input_access_code
    form <= html.BR()

    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    form <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value="")
    form <= input_access_restriction_reliability
    form <= html.BR()

    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    form <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value="")
    form <= input_access_restriction_regularity
    form <= html.BR()

    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    form <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value="")
    form <= input_access_restriction_performance
    form <= html.BR()

    legend_title_access = html.LEGEND("Avancement de la partie - ne peuvent plus être changés la partie créée")
    legend_title_access.style = {
        'color': 'red',
    }
    form <= legend_title_access

    legend_nb_max_cycles_to_play = html.LEGEND("maximum de cycles (années)", title="Combien d'années à jouer au plus ?")
    form <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=DEFAULT_NB_CYCLES)
    form <= input_nb_max_cycles_to_play
    form <= html.BR()

    legend_victory_centers = html.LEGEND("victoire en centres", title="Combien de centres sont nécessaires pour gagner ?")
    form <= legend_victory_centers
    input_victory_centers = html.INPUT(type="number", value=DEFAULT_VICTORY_CENTERS)
    form <= input_victory_centers
    form <= html.BR()

    form <= html.BR()

    input_create_game = html.INPUT(type="submit", value="créer la partie")
    input_create_game.bind("click", create_game_callback)
    form <= input_create_game

    my_sub_panel <= form


def change_description_game():
    """ change_description_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    description_loaded = None

    def change_description_reload():
        """ change_description_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal description_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la description de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la description de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            description_loaded = req_result['description']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_description_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la description de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la description de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La description a été modifiée : {messages}", remove_after=config.REMOVE_AFTER)

        description = input_description.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'description': description,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game description : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_description_game()

    status = change_description_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_description = html.LEGEND("description", title="Cela peut être long. Exemple : 'une partie entre étudiants de l'ETIAM'")
    form <= legend_description

    input_description = html.TEXTAREA(type="text", rows=5, cols=80)
    input_description <= description_loaded
    form <= input_description
    form <= html.BR()

    form <= html.BR()

    input_change_description_game = html.INPUT(type="submit", value="changer la description de la partie")
    input_change_description_game.bind("click", change_description_game_callback)
    form <= input_change_description_game

    my_sub_panel <= form


def change_access_parameters_game():
    """ change_access_parameters_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    access_code_loaded = None
    access_restriction_reliability_loaded = None
    access_restriction_regularity_loaded = None
    access_restriction_performance_loaded = None

    def change_access_parameters_reload():
        """ change_access_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal access_code_loaded
            nonlocal access_restriction_reliability_loaded
            nonlocal access_restriction_regularity_loaded
            nonlocal access_restriction_performance_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du paramètre d'accès à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du paramètre d'accès à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            access_code_loaded = req_result['access_code']
            access_restriction_reliability_loaded = req_result['access_restriction_reliability']
            access_restriction_regularity_loaded = req_result['access_restriction_regularity']
            access_restriction_performance_loaded = req_result['access_restriction_performance']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_access_parameters_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du paramètre d'accès à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du paramètre d'accès à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Les paramètres d'accès ont été modifiés : {messages}", remove_after=config.REMOVE_AFTER)

        access_code = input_access_code.value
        access_restriction_reliability = input_access_restriction_reliability.value
        access_restriction_regularity = input_access_restriction_regularity.value
        access_restriction_performance = input_access_restriction_performance.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'access_code': access_code,
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game access parameters : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_access_parameters_game()

    status = change_access_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_access_code = html.LEGEND("code accès", title="Code d'accès à la partie")
    form <= legend_access_code
    input_access_code = html.INPUT(type="number", value=access_code_loaded)
    form <= input_access_code
    form <= html.BR()

    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    form <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability_loaded)
    form <= input_access_restriction_reliability
    form <= html.BR()

    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    form <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity_loaded)
    form <= input_access_restriction_regularity
    form <= html.BR()

    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    form <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance_loaded)
    form <= input_access_restriction_performance
    form <= html.BR()

    form <= html.BR()

    input_change_access_game = html.INPUT(type="submit", value="changer les paramètres d'accès à la partie")
    input_change_access_game.bind("click", change_access_parameters_game_callback)
    form <= input_change_access_game

    my_sub_panel <= form


def change_deadline_game():
    """ change_deadline_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    deadline_loaded_day = None
    deadline_loaded_hour = None

    def change_deadline_reload():
        """ change_deadline_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal deadline_loaded_day
            nonlocal deadline_loaded_hour

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la date limite de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la date limite de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            # convert deadline from server to humand editable deadline
            deadline_loaded = req_result['deadline']
            datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
            deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
            deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été modifiée : {messages}", remove_after=config.REMOVE_AFTER)

        # convert this human entered deadline to the deadline the server understands
        deadline_day_part = input_deadline_day.value
        deadline_hour_part = input_deadline_hour.value
        deadline_datetime_str = f"{deadline_day_part} {deadline_hour_part}"
        deadline_datetime = datetime.datetime.strptime(deadline_datetime_str, "%Y-%m-%d %H:%M")
        timestamp = deadline_datetime.replace(tzinfo=datetime.timezone.utc).timestamp()
        deadline = int(timestamp)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'deadline': deadline,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_deadline_game()

    status = change_deadline_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    dl_gmt = html.B("ATTENTION : vous devez entrer une date limite en temps GMT")
    special_legend = html.LEGEND(dl_gmt)
    form <= special_legend

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

    special_legend = html.CODE(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    form <= special_legend
    form <= html.BR()

    form <= html.BR()

    legend_deadline_day = html.LEGEND("Jour de la date limite (DD/MM/YYYY - ou selon les réglages du navigateur)", title="La date limite. Dernier jour pour soumettre les ordres. Après le joueur est en retard.")
    form <= legend_deadline_day

    input_deadline_day = html.INPUT(type="date", value=deadline_loaded_day)
    form <= input_deadline_day
    form <= html.BR()

    form <= html.BR()

    legend_deadline_hour = html.LEGEND("Heure de la date limite (hh:mm ou selon les réglages du navigateur)")
    form <= legend_deadline_hour

    input_deadline_hour = html.INPUT(type="time", value=deadline_loaded_hour)
    form <= input_deadline_hour
    form <= html.BR()

    form <= html.BR()

    input_change_deadline_game = html.INPUT(type="submit", value="changer la date limite de la partie")
    input_change_deadline_game.bind("click", change_deadline_game_callback)
    form <= input_change_deadline_game

    my_sub_panel <= form


def change_pace_parameters_game():
    """ change_pace_parameters_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    speed_moves_loaded = None
    cd_possible_moves_loaded = None
    speed_retreats_loaded = None
    cd_possible_retreats_loaded = None
    speed_adjustments_loaded = None
    cd_possible_builds_loaded = None
    cd_possible_removals_loaded = None
    play_weekend_loaded = None

    def change_pace_parameters_reload():
        """ change_pace_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal speed_moves_loaded
            nonlocal cd_possible_moves_loaded
            nonlocal speed_retreats_loaded
            nonlocal cd_possible_retreats_loaded
            nonlocal speed_adjustments_loaded
            nonlocal cd_possible_builds_loaded
            nonlocal cd_possible_removals_loaded
            nonlocal play_weekend_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du rythme de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du rythme de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            speed_moves_loaded = req_result['speed_moves']
            cd_possible_moves_loaded = req_result['cd_possible_moves']
            speed_retreats_loaded = req_result['speed_retreats']
            cd_possible_retreats_loaded = req_result['cd_possible_retreats']
            speed_adjustments_loaded = req_result['speed_adjustments']
            cd_possible_builds_loaded = req_result['cd_possible_builds']
            cd_possible_removals_loaded = req_result['cd_possible_removals']
            play_weekend_loaded = req_result['play_weekend']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_pace_parameters_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du rythme à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du rythme à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Les paramètres de cadence ont été modifiés : {messages}", remove_after=config.REMOVE_AFTER)

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
        cd_possible_removals = int(input_cd_possible_removals.checked)
        play_weekend = int(input_play_weekend.checked)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'speed_moves': speed_moves,
            'cd_possible_moves': cd_possible_moves,
            'speed_retreats': speed_retreats,
            'cd_possible_retreats': cd_possible_retreats,
            'speed_adjustments': speed_adjustments,
            'cd_possible_builds': cd_possible_builds,
            'cd_possible_removals': cd_possible_removals,
            'play_weekend': play_weekend,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game pace parameters : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_pace_parameters_game()

    status = change_pace_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    # moves

    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre de jours avant la date limite de mouvements")
    form <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves_loaded)
    form <= input_speed_moves
    form <= html.BR()

    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    form <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=cd_possible_moves_loaded)
    form <= input_cd_possible_moves
    form <= html.BR()

    # retreats

    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre de jours avant la date limite de retraites")
    form <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats_loaded)
    form <= input_speed_retreats
    form <= html.BR()

    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    form <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=cd_possible_retreats_loaded)
    form <= input_cd_possible_retreats
    form <= html.BR()

    # adjustments

    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre de jours avant la date limite d'ajustements")
    form <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments_loaded)
    form <= input_speed_adjustments
    form <= html.BR()

    # builds

    legend_cd_possible_builds = html.LEGEND("DC possible constructions", title="Désordre civil possible pour une résolution d'ajustements - constructions")
    form <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=cd_possible_builds_loaded)
    form <= input_cd_possible_builds
    form <= html.BR()

    # removals

    legend_cd_possible_removals = html.LEGEND("DC possible suppressions", title="Désordre civil possible pour une résolution d'ajustements - suppressions")
    form <= legend_cd_possible_removals
    input_cd_possible_removals = html.INPUT(type="checkbox", checked=cd_possible_removals_loaded)
    form <= input_cd_possible_removals
    form <= html.BR()

    # ---

    legend_play_weekend = html.LEGEND("jeu weekend", title="La partie est jouée en fin de semaine")
    form <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=play_weekend_loaded)
    form <= input_play_weekend
    form <= html.BR()

    form <= html.BR()

    input_change_pace_game = html.INPUT(type="submit", value="changer le rythme de la partie")
    input_change_pace_game.bind("click", change_pace_parameters_game_callback)
    form <= input_change_pace_game

    my_sub_panel <= form


def change_state_game():
    """ change_state_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    state_loaded = None

    def change_state_reload():
        """ change_state_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal state_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'état de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'état de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            state_loaded = req_result['current_state']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_state_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'état de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'état de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'état de la partie a été modifié : {messages}", remove_after=config.REMOVE_AFTER)

        state = config.STATE_CODE_TABLE[input_state.value]

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'current_state': state,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_state_game()

    status = change_state_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_state = html.LEGEND("état", title="Etat de la partie : en attente, en cours ou terminée.")
    form <= legend_state

    input_state = html.SELECT(type="select-one", value="")
    for possible_state in config.STATE_CODE_TABLE:
        option = html.OPTION(possible_state)
        if config.STATE_CODE_TABLE[possible_state] == state_loaded:
            option.selected = True
        input_state <= option
    form <= input_state
    form <= html.BR()

    form <= html.BR()

    input_change_state_game = html.INPUT(type="submit", value="changer l'état de la partie")
    input_change_state_game.bind("click", change_state_game_callback)
    form <= input_change_state_game

    my_sub_panel <= form


def delete_game():
    """ delete_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    def delete_game_callback(_, dialog):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppresssion de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppresssion de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La partie a été supprimée : {messages}", remove_after=config.REMOVE_AFTER)
            selection.unselect_game()

        if dialog:
            dialog.close()

        json_dict = {
            'pseudo': pseudo
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # deleting game : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_game_callback_confirm(_):

        # For some reason does not work, confirmation window dissapears
        #  dialog = Dialog(f"On supprime vraiment la partie {game} ?", ok_cancel=True)
        #  dialog.ok_button.bind("click", lambda e, d=dialog: delete_game_callback(e, d))
        #  dialog.cancel_button.bind("click", lambda e, d=dialog: d.close())

        # called directly
        delete_game_callback(_, None)

    form = html.FORM()

    input_delete_game = html.INPUT(type="submit", value="supprimer la partie")
    input_delete_game.bind("click", delete_game_callback_confirm)
    form <= input_delete_game

    my_sub_panel <= form


my_panel = html.DIV(id="games")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'créer':
        create_game()
    if item_name == 'changer description':
        change_description_game()
    if item_name == 'changer paramètres accès':
        change_access_parameters_game()
    if item_name == 'changer date limite':
        change_deadline_game()
    if item_name == 'changer paramètre cadence':
        change_pace_parameters_game()
    if item_name == 'changer état':
        change_state_game()
    if item_name == 'supprimer':
        delete_game()
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
