""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import selection
import index  # circular import

OPTIONS = ['Créer', 'Changer description', 'Changer anonymat', 'Changer accès messagerie', 'Changer scorage', 'Changer paramètres accès', 'Changer date limite', 'Changer paramètres cadence', 'Changer état', 'Supprimer']

MAX_LEN_GAME_NAME = 50
MAX_LEN_VARIANT_NAME = 20

DEFAULT_VARIANT = 'standard'
DEFAULT_SCORING_CODE = "CDIP"
DEFAULT_DEADLINE_TIME = 21
DEFAULT_GRACE_DURATION = 24
DEFAULT_SPEED_MOVES = 72
DEFAULT_SPEED_OTHERS = 24
DEFAULT_VICTORY_CENTERS = 18
DEFAULT_NB_CYCLES = 7


def information_about_input():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= "Survolez les titres pour pour plus de détails"
    return information


def information_about_playing():
    """ information_about_playing """

    information = html.DIV(Class='note')
    information <= html.B("Vous voulez juste jouer ? ")
    information <= html.BR()
    information <= "Créez-la partie et démissionnez ensuite de l'arbitrage (appariement). Un arbitre sera alloué automatiquement..."
    return information


def create_game(json_dict):
    """ create_game """

    # load previous values if applicable
    name = json_dict['name'] if json_dict and 'name' in json_dict else None
    variant = json_dict['variant'] if json_dict and 'variant' in json_dict else None
    archive = json_dict['archive'] if json_dict and 'archive' in json_dict else None
    used_for_elo = json_dict['used_for_elo'] if json_dict and 'used_for_elo' in json_dict else None
    manual = json_dict['manual'] if json_dict and 'manual' in json_dict else None
    anonymous = json_dict['anonymous'] if json_dict and 'anonymous' in json_dict else None
    nomessage_game = json_dict['nomessage_game'] if json_dict and 'nomessage_game' in json_dict else None
    nopress_game = json_dict['nopress_game'] if json_dict and 'nopress_game' in json_dict else None
    fast = json_dict['fast'] if json_dict and 'fast' in json_dict else None
    scoring_code = json_dict['scoring_code'] if json_dict and 'scoring_code' in json_dict else None
    deadline_hour = json_dict['deadline_hour'] if json_dict and 'deadline_hour' in json_dict else None
    deadline_sync = json_dict['deadline_sync'] if json_dict and 'deadline_sync' in json_dict else None
    grace_duration = json_dict['grace_duration'] if json_dict and 'grace_duration' in json_dict else None
    speed_moves = json_dict['speed_moves'] if json_dict and 'speed_moves' in json_dict else None
    cd_possible_moves = json_dict['cd_possible_moves'] if json_dict and 'cd_possible_moves' in json_dict else None
    speed_retreats = json_dict['speed_retreats'] if json_dict and 'speed_retreats' in json_dict else None
    cd_possible_retreats = json_dict['cd_possible_retreats'] if json_dict and 'cd_possible_retreats' in json_dict else None
    speed_adjustments = json_dict['speed_adjustments'] if json_dict and 'speed_adjustments' in json_dict else None
    cd_possible_builds = json_dict['cd_possible_builds'] if json_dict and 'cd_possible_builds' in json_dict else None
    play_weekend = json_dict['play_weekend'] if json_dict and 'play_weekend' in json_dict else None
    access_restriction_reliability = json_dict['access_restriction_reliability'] if json_dict and 'access_restriction_reliability' in json_dict else None
    access_restriction_regularity = json_dict['access_restriction_regularity'] if json_dict and 'access_restriction_regularity' in json_dict else None
    access_restriction_performance = json_dict['access_restriction_performance'] if json_dict and 'access_restriction_performance' in json_dict else None
    nb_max_cycles_to_play = json_dict['nb_max_cycles_to_play'] if json_dict and 'nb_max_cycles_to_play' in json_dict else None
    victory_centers = json_dict['victory_centers'] if json_dict and 'victory_centers' in json_dict else None

    def create_game_callback(_):
        """ create_game_callback """

        nonlocal name
        nonlocal variant
        nonlocal archive
        nonlocal used_for_elo
        nonlocal manual
        nonlocal anonymous
        nonlocal nomessage_game
        nonlocal nopress_game
        nonlocal fast
        nonlocal scoring_code
        nonlocal deadline_hour
        nonlocal deadline_sync
        nonlocal grace_duration
        nonlocal speed_moves
        nonlocal cd_possible_moves
        nonlocal speed_retreats
        nonlocal cd_possible_retreats
        nonlocal speed_adjustments
        nonlocal cd_possible_builds
        nonlocal play_weekend
        nonlocal access_restriction_reliability
        nonlocal access_restriction_regularity
        nonlocal access_restriction_performance
        nonlocal nb_max_cycles_to_play
        nonlocal victory_centers

        def reply_callback(req):
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
            alert("Maintenant vous devez la sélectionner par le menu 'Sélectionner partie'")

        # get values from user input

        name = input_name.value
        variant = input_variant.value
        archive = int(input_archive.checked)
        used_for_elo = int(input_used_for_elo.checked)
        manual = int(input_manual.checked)
        anonymous = int(input_anonymous.checked)
        nomessage_game = int(input_nomessage_game.checked)
        nopress_game = int(input_nopress_game.checked)
        fast = int(input_fast.checked)
        scoring_code = config.SCORING_CODE_TABLE[input_scoring.value]

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

        specific_data = ""
        if archive:
            specific_data += "archive "
        if manual:
            specific_data += "manuelle "
        if anonymous:
            specific_data += "anonyme "
        if nomessage_game:
            specific_data += "sans message "
        if nopress_game:
            specific_data += "sans presse "
        if fast:
            specific_data += "en direct "
        if not specific_data:
            specific_data = "(sans particularité) "

        description = f"Partie créée le {time_creation_str} (gmt) par {pseudo} variante {variant}. Cette partie est {specific_data}. Scorage {scoring_code}."
        state = 0

        # make data strucuture
        json_dict = {
            'name': name,
            'variant': variant,
            'archive': archive,
            'used_for_elo': used_for_elo,
            'manual': manual,
            'anonymous': anonymous,
            'nomessage_game': nomessage_game,
            'nopress_game': nopress_game,
            'fast': fast,
            'scoring': scoring_code,
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
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,
            'nb_max_cycles_to_play': nb_max_cycles_to_play,
            'victory_centers': victory_centers,
            'description': description,
            'current_state': state,
            'pseudo': pseudo
        }

        # start checking data

        if not name:
            alert("Nom de partie manquant")
            MY_SUB_PANEL.clear()
            create_game(json_dict)
            return

        if len(name) > MAX_LEN_GAME_NAME:
            alert("Nom de partie trop long")
            MY_SUB_PANEL.clear()
            create_game(json_dict)
            return

        if not variant:
            alert("Nom de variante manquante")
            MY_SUB_PANEL.clear()
            create_game(json_dict)
            return

        if len(variant) > MAX_LEN_VARIANT_NAME:
            alert("Nom de variante trop long")
            MY_SUB_PANEL.clear()
            create_game(json_dict)
            return

        # send to server

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"

        # creating a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_game(json_dict)

    MY_SUB_PANEL <= html.H3("Création de partie")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    MY_SUB_PANEL <= information_about_playing()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= information_about_input()

    form = html.FORM()

    legend_title_main = html.H3("Paramètres principaux de la partie - ne peuvent plus être changés la partie créée")
    form <= legend_title_main

    form <= html.DIV("Pas d'accents, d'espaces ni de tirets dans le nom de la partie", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de la partie (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=name if name is not None else "", size=MAX_LEN_GAME_NAME)
    fieldset <= input_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("variante", title="(imposée pour me moment)")
    fieldset <= legend_variant
    input_variant = html.INPUT(type="select-one", readonly=True, value=DEFAULT_VARIANT)
    fieldset <= input_variant
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_archive = html.LEGEND("archive", title="Partie pour les archives - la partie n'est pas jouée - l'arbitre passe tous les ordres")
    fieldset <= legend_archive
    input_archive = html.INPUT(type="checkbox", checked=bool(archive) if archive is not None else False)
    fieldset <= input_archive
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_used_for_elo = html.LEGEND("utilisée pour le élo", title="Partie sérieuse - les résultats de la partie comptent pour le calcul du élo sur le site")
    fieldset <= legend_used_for_elo
    input_used_for_elo = html.INPUT(type="checkbox", checked=bool(used_for_elo) if used_for_elo is not None else True)
    fieldset <= input_used_for_elo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_manual = html.LEGEND("casting manuel", title="L'arbitre attribue les rôles dans la partie et non le système")
    fieldset <= legend_manual
    input_manual = html.INPUT(type="checkbox", checked=bool(manual) if manual is not None else False)
    fieldset <= input_manual
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_fast = html.LEGEND("en direct", title="Le calcul des dates limites se fait en minutes au lieu d'heures. (Ne cocher que pour une partie comme sur un plateau)")
    fieldset <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=bool(fast) if fast is not None else False)
    fieldset <= input_fast
    form <= fieldset

    title_terms = html.H3("Modalités de la partie - peuvent être changées la partie créée")
    form <= title_terms

    fieldset = html.FIELDSET()
    legend_anonymous = html.LEGEND("anonyme", title="Les identités des joueurs ne sont pas révélées avant la fin de la partie")
    fieldset <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=bool(anonymous) if anonymous is not None else False)
    fieldset <= input_anonymous
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nomessage_game = html.LEGEND("pas de message privé", title="Les joueurs ne peuvent pas communiquer (négocier) par message privé avant la fin de la partie")
    fieldset <= legend_nomessage_game
    input_nomessage_game = html.INPUT(type="checkbox", checked=bool(nomessage_game) if nomessage_game is not None else False)
    fieldset <= input_nomessage_game
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nopress_game = html.LEGEND("pas de message public", title="Les joueurs ne peuvent pas communiquer (déclarer) par message public avant la fin de la partie")
    fieldset <= legend_nopress_game
    input_nopress_game = html.INPUT(type="checkbox", checked=bool(nopress_game) if nopress_game is not None else False)
    fieldset <= input_nopress_game
    form <= fieldset

    form <= html.DIV("Les paramètres 'pas de message public/privé' sont fixés pour l'exportation des modalités de la partie, il restent toutefois modifiables à tout moment par l'arbitre dans leur version applicable...", Class='note')

    title_scoring = html.H3("Système de marque")
    form <= title_scoring

    # special : la marque

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="La méthode pour compter les points (applicable aux parties en tournoi uniquement)")
    fieldset <= legend_scoring
    input_scoring = html.SELECT(type="select-one", value="")

    for scoring_name in config.SCORING_CODE_TABLE:
        option = html.OPTION(scoring_name)
        if config.SCORING_CODE_TABLE[scoring_name] == (scoring_code if scoring_code is not None else DEFAULT_SCORING_CODE):
            option.selected = True
        input_scoring <= option

    fieldset <= input_scoring
    form <= fieldset

    title_pace = html.H3("Cadence de la partie")
    form <= title_pace

    # deadline

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("heure de date limite", title="Heure GMT de la journée à laquelle placer les dates limites")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="number", value=deadline_hour if deadline_hour is not None else DEFAULT_DEADLINE_TIME)
    fieldset <= input_deadline_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_sync = html.LEGEND("synchronisation des dates limites", title="Faut-il synchroniser les dates limites à une heure donnée")
    fieldset <= legend_deadline_sync
    input_deadline_sync = html.INPUT(type="checkbox", checked=bool(deadline_sync) if deadline_sync is not None else True)
    fieldset <= input_deadline_sync
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_grace_duration = html.LEGEND("durée de grâce", title="Nombre d'heures (minutes pour une partie en direct) alloués avant fin de la grâce")
    fieldset <= legend_grace_duration
    input_grace_duration = html.INPUT(type="number", value=grace_duration if grace_duration is not None else DEFAULT_GRACE_DURATION)
    fieldset <= input_grace_duration
    form <= fieldset

    # moves

    fieldset = html.FIELDSET()
    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de mouvements")
    fieldset <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves if speed_moves is not None else DEFAULT_SPEED_MOVES)
    fieldset <= input_speed_moves
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    fieldset <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=bool(cd_possible_moves) if cd_possible_moves is not None else False)
    fieldset <= input_cd_possible_moves
    form <= fieldset

    # retreats

    fieldset = html.FIELDSET()
    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de retraites")
    fieldset <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats if speed_retreats is not None else DEFAULT_SPEED_OTHERS)
    fieldset <= input_speed_retreats
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    fieldset <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=bool(cd_possible_retreats) if cd_possible_retreats is not None else False)
    fieldset <= input_cd_possible_retreats
    form <= fieldset

    # adjustments

    fieldset = html.FIELDSET()
    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite d'ajustements")
    fieldset <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments if speed_adjustments is not None else DEFAULT_SPEED_OTHERS)
    fieldset <= input_speed_adjustments
    form <= fieldset

    # builds/removals

    fieldset = html.FIELDSET()
    legend_cd_possible_builds = html.LEGEND("DC possible ajustements", title="Désordre civil possible pour une résolution d'ajustements")
    fieldset <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=bool(cd_possible_builds) if cd_possible_builds is not None else False)
    fieldset <= input_cd_possible_builds
    form <= fieldset

    # ---

    fieldset = html.FIELDSET()
    legend_play_weekend = html.LEGEND("jeu weekend", title="La date limite peut elle se trouver en fin de semaine")
    fieldset <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=bool(play_weekend) if play_weekend is not None else False)
    fieldset <= input_play_weekend
    form <= fieldset

    title_access = html.H3("Accès à la partie - ne peuvent plus être changés la partie démarrée")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    fieldset <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability if access_restriction_reliability is not None else "")
    fieldset <= input_access_restriction_reliability
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    fieldset <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity if access_restriction_regularity is not None else "")
    fieldset <= input_access_restriction_regularity
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    fieldset <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance if access_restriction_performance is not None else "")
    fieldset <= input_access_restriction_performance
    form <= fieldset

    title_access = html.H3("Fin de la partie - ne peuvent plus être changés la partie créée")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_nb_max_cycles_to_play = html.LEGEND("maximum de cycles (années)", title="Combien d'années à jouer au plus ?")
    fieldset <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=nb_max_cycles_to_play if nb_max_cycles_to_play is not None else DEFAULT_NB_CYCLES)
    fieldset <= input_nb_max_cycles_to_play
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_victory_centers = html.LEGEND("victoire en centres", title="Combien de centres sont nécessaires pour gagner ?")
    fieldset <= legend_victory_centers
    input_victory_centers = html.INPUT(type="number", value=victory_centers if victory_centers is not None else DEFAULT_VICTORY_CENTERS)
    fieldset <= input_victory_centers
    form <= fieldset

    form <= html.BR()

    input_create_game = html.INPUT(type="submit", value="créer la partie")
    input_create_game.bind("click", create_game_callback)
    form <= input_create_game

    MY_SUB_PANEL <= form


def change_description_game():
    """ change_description_game """

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

        json_dict = {}

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
        MY_SUB_PANEL.clear()
        change_description_game()

    MY_SUB_PANEL <= html.H3("Changement de la description")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_description_reload()
    if not status:
        return

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

    input_change_description_game = html.INPUT(type="submit", value="changer la description de la partie")
    input_change_description_game.bind("click", change_description_game_callback)
    form <= input_change_description_game

    MY_SUB_PANEL <= form


def change_anonymity_game():
    """ change_anonymity_game """

    # declare the values
    anonymity_loaded = None

    def change_anonymity_reload():
        """ change_anonymity_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal anonymity_loaded
            req_result = json.loads(req.text)

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

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_anonymity_games_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification anonymat de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification anonymat de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'accès à l'anonymat a été modifié : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'anonymous': input_anonymous.checked,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_anonymity_game()

    MY_SUB_PANEL <= html.H3("Changement de l'anonymat sur la partie")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_anonymity_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_anonymous = html.LEGEND("anonyme", title="Les identités des joueurs ne sont pas révélées avant la fin de la partie")
    fieldset <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=anonymity_loaded)
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_change_anonymity_game = html.INPUT(type="submit", value="changer l'anonymat de la partie")
    input_change_anonymity_game.bind("click", change_anonymity_games_callback)
    form <= input_change_anonymity_game

    MY_SUB_PANEL <= form


def change_access_messages_game():
    """ change_access_messages_game """

    # declare the values
    access_nopress_loaded = None
    access_nomessage_loaded = None

    def change_access_messages_reload():
        """ change_access_messages_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal access_nopress_loaded
            nonlocal access_nomessage_loaded
            req_result = json.loads(req.text)

            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération acces messagerie de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération acces messagerie de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            access_nopress_loaded = req_result['nopress_current']
            access_nomessage_loaded = req_result['nomessage_current']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_access_messages_games_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification acces messagerie de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification acces messagerie de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'accès à la messagerie a été modifié : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'nopress_current': input_nopress.checked,
            'nomessage_current': input_nomessage.checked,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_access_messages_game()

    MY_SUB_PANEL <= html.H3("Changement de l'accès aux messagerie")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_access_messages_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nopress = html.LEGEND("pas de message public", title="Les joueurs ne peuvent pas communiquer (déclarer) par message public avant la fin de la partie")
    fieldset <= legend_nopress
    input_nopress = html.INPUT(type="checkbox", checked=access_nopress_loaded)
    fieldset <= input_nopress
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nomessage = html.LEGEND("pas de message privé", title="Les joueurs ne peuvent pas communiquer (négocier) par message privé avant la fin de la partie")
    fieldset <= legend_nomessage
    input_nomessage = html.INPUT(type="checkbox", checked=access_nomessage_loaded)
    fieldset <= input_nomessage
    form <= fieldset

    form <= html.BR()

    input_change_message_game = html.INPUT(type="submit", value="changer l'accès aux messages publics et privés de la partie")
    input_change_message_game.bind("click", change_access_messages_games_callback)
    form <= input_change_message_game

    MY_SUB_PANEL <= form


def change_scoring_game():
    """ change_scoring_game """

    # declare the values
    scoring_code_loaded = None

    def change_scoring_reload():
        """ change_scoring_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal scoring_code_loaded
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du scorage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du scorage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            scoring_code_loaded = req_result['scoring']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_scoring_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du scorage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du scorage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le scorage a été modifié : {messages}", remove_after=config.REMOVE_AFTER)

        scoring_code = config.SCORING_CODE_TABLE[input_scoring.value]

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'scoring': scoring_code,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_scoring_game()

    MY_SUB_PANEL <= html.H3("Changement du scorage")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_scoring_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scoring", title="La méthode pour compter les points (applicable aux parties en tournoi uniquement)")
    fieldset <= legend_scoring
    input_scoring = html.SELECT(type="select-one", value="")

    for scoring_name in config.SCORING_CODE_TABLE:
        option = html.OPTION(scoring_name)
        if config.SCORING_CODE_TABLE[scoring_name] == scoring_code_loaded:
            option.selected = True
        input_scoring <= option

    fieldset <= input_scoring
    form <= fieldset

    form <= html.BR()

    input_change_scoring_game = html.INPUT(type="submit", value="changer le scorage de la partie")
    input_change_scoring_game.bind("click", change_scoring_game_callback)
    form <= input_change_scoring_game

    MY_SUB_PANEL <= form


def change_access_parameters_game():
    """ change_access_parameters_game """

    # declare the values
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
            nonlocal status
            nonlocal access_restriction_reliability_loaded
            nonlocal access_restriction_regularity_loaded
            nonlocal access_restriction_performance_loaded
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des paramètres d'accès à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des paramètres d'accès à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            access_restriction_reliability_loaded = req_result['access_restriction_reliability']
            access_restriction_regularity_loaded = req_result['access_restriction_regularity']
            access_restriction_performance_loaded = req_result['access_restriction_performance']

        json_dict = {}

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

        access_restriction_reliability = input_access_restriction_reliability.value
        access_restriction_regularity = input_access_restriction_regularity.value
        access_restriction_performance = input_access_restriction_performance.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
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
        MY_SUB_PANEL.clear()
        change_access_parameters_game()

    MY_SUB_PANEL <= html.H3("Changement des paramètres d'accès")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_access_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    fieldset <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability_loaded)
    fieldset <= input_access_restriction_reliability
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    fieldset <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity_loaded)
    fieldset <= input_access_restriction_regularity
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    fieldset <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance_loaded)
    fieldset <= input_access_restriction_performance
    form <= fieldset

    form <= html.BR()

    input_change_access_game = html.INPUT(type="submit", value="changer les paramètres d'accès à la partie")
    input_change_access_game.bind("click", change_access_parameters_game_callback)
    form <= input_change_access_game

    MY_SUB_PANEL <= form


def change_deadline_game():
    """ change_deadline_game """

    # declare the values
    deadline_loaded = None

    def change_deadline_reload():
        """ change_deadline_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal deadline_loaded
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

        json_dict = {}

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
        MY_SUB_PANEL.clear()
        change_deadline_game()

    MY_SUB_PANEL <= html.H3("Changement de la date limite")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_deadline_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    dl_gmt = html.DIV("ATTENTION : vous devez entrer une date limite en temps GMT", Class='important')
    special_legend = html.LEGEND(dl_gmt)
    form <= special_legend
    form <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

    special_info = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    form <= special_info
    form <= html.BR()

    # convert 'deadline_loaded' to human editable format

    datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
    deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
    deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"

    fieldset = html.FIELDSET()
    legend_deadline_day = html.LEGEND("Jour de la date limite (DD/MM/YYYY - ou selon les réglages du navigateur)", title="La date limite. Dernier jour pour soumettre les ordres. Après le joueur est en retard.")
    fieldset <= legend_deadline_day
    input_deadline_day = html.INPUT(type="date", value=deadline_loaded_day)
    fieldset <= input_deadline_day
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("Heure de la date limite (hh:mm ou selon les réglages du navigateur)")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="time", value=deadline_loaded_hour)
    fieldset <= input_deadline_hour
    form <= fieldset

    form <= html.BR()

    input_change_deadline_game = html.INPUT(type="submit", value="changer la date limite de la partie")
    input_change_deadline_game.bind("click", change_deadline_game_callback)
    form <= input_change_deadline_game

    MY_SUB_PANEL <= form


def change_pace_parameters_game():
    """ change_pace_parameters_game """

    # declare the values
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

    def change_pace_parameters_reload():
        """ change_pace_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
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
            'pseudo': pseudo,
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
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_pace_parameters_game()

    MY_SUB_PANEL <= html.H3("Changement de paramètres de cadence")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_pace_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    # deadline related

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("heure de date limite", title="Heure GMT de la journée à laquelle placer les dates limites")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="number", value=deadline_hour_loaded)
    fieldset <= input_deadline_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_sync = html.LEGEND("synchronisation des date limites", title="Faut-il synchroniser les dates limites à une heure donnée")
    fieldset <= legend_deadline_sync
    input_deadline_sync = html.INPUT(type="checkbox", checked=deadline_sync_loaded)
    fieldset <= input_deadline_sync
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_grace_duration = html.LEGEND("durée de grâce", title="Nombre d'heures (minutes pour une partie en direct) alloués avant fin de la grâce")
    fieldset <= legend_grace_duration
    input_grace_duration = html.INPUT(type="number", value=grace_duration_loaded)
    fieldset <= input_grace_duration
    form <= fieldset

    # moves

    fieldset = html.FIELDSET()
    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de mouvements")
    fieldset <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves_loaded)
    fieldset <= input_speed_moves
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    fieldset <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=cd_possible_moves_loaded)
    fieldset <= input_cd_possible_moves
    form <= fieldset

    # retreats

    fieldset = html.FIELDSET()
    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de retraites")
    fieldset <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats_loaded)
    fieldset <= input_speed_retreats
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    fieldset <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=cd_possible_retreats_loaded)
    fieldset <= input_cd_possible_retreats
    form <= fieldset

    # adjustments

    fieldset = html.FIELDSET()
    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite d'ajustements")
    fieldset <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments_loaded)
    fieldset <= input_speed_adjustments
    form <= fieldset

    # builds/removals

    fieldset = html.FIELDSET()
    legend_cd_possible_builds = html.LEGEND("DC possible ajustements", title="Désordre civil possible pour une résolution d'ajustements")
    fieldset <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=cd_possible_builds_loaded)
    fieldset <= input_cd_possible_builds
    form <= fieldset

    # ---

    fieldset = html.FIELDSET()
    legend_play_weekend = html.LEGEND("jeu weekend", title="La date limite peut elle se trouver en fin de semaine")
    fieldset <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=play_weekend_loaded)
    fieldset <= input_play_weekend
    form <= fieldset

    form <= html.BR()

    input_change_pace_game = html.INPUT(type="submit", value="changer le rythme de la partie")
    input_change_pace_game.bind("click", change_pace_parameters_game_callback)
    form <= input_change_pace_game

    MY_SUB_PANEL <= form


def change_state_game():
    """ change_state_game """

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

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def cancel_change_state_game_callback(_, dialog):
        """ cancel_delete_account_callback """
        dialog.close()

    def change_state_game_callback(_, dialog, expected_state):

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

        if dialog is not None:
            dialog.close()

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'current_state': expected_state,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_state_game()

    def change_state_game_callback_confirm(_, expected_state):
        dialog = Dialog(f"On arrête vraiment la partie {game} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, es=expected_state: change_state_game_callback(e, d, es))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_change_state_game_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        change_state_game()

    MY_SUB_PANEL <= html.H3("Changement d'état")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = change_state_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_state = html.LEGEND("état", title="Etat de la partie : en attente, en cours, terminée ou distinguée.")
    fieldset <= legend_state

    if state_loaded == 0:
        input_start_game = html.INPUT(type="submit", value="démarrer la partie")
        input_start_game.bind("click", lambda e, s=1: change_state_game_callback(e, None, s))
        form <= input_start_game

    if state_loaded == 1:
        input_stop_game = html.INPUT(type="submit", value="arrêter la partie")
        input_stop_game.bind("click", lambda e, s=2: change_state_game_callback_confirm(e, s))
        form <= input_stop_game

    if state_loaded == 2:
        input_stop_game = html.INPUT(type="submit", value="distinguer la partie")
        input_stop_game.bind("click", lambda e, s=3: change_state_game_callback(e, None, s))
        form <= input_stop_game

    if state_loaded == 3:
        input_stop_game = html.INPUT(type="submit", value="ne plus distinguer la partie")
        input_stop_game.bind("click", lambda e, s=2: change_state_game_callback(e, None, s))
        form <= input_stop_game

    MY_SUB_PANEL <= form


def delete_game():
    """ delete_game """

    def cancel_delete_game_callback(_, dialog):
        """ cancel_delete_game_callback """
        dialog.close()

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

            # go to select another game
            index.load_option(None, 'Sélectionner partie')

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
        """ delete_game_callback_confirm """

        dialog = Dialog(f"On supprime vraiment la partie {game} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_game_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_game_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        delete_game()

    MY_SUB_PANEL <= html.H3("Suppression")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    input_delete_game = html.INPUT(type="submit", value="supprimer la partie")
    input_delete_game.bind("click", delete_game_callback_confirm)
    form <= input_delete_game

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

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id="games")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Créer':
        create_game(None)
    if item_name == 'Changer description':
        change_description_game()
    if item_name == 'Changer anonymat':
        change_anonymity_game()
    if item_name == 'Changer accès messagerie':
        change_access_messages_game()
    if item_name == 'Changer scorage':
        change_scoring_game()
    if item_name == 'Changer paramètres accès':
        change_access_parameters_game()
    if item_name == 'Changer date limite':
        change_deadline_game()
    if item_name == 'Changer paramètres cadence':
        change_pace_parameters_game()
    if item_name == 'Changer état':
        change_state_game()
    if item_name == 'Supprimer':
        delete_game()

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
    ITEM_NAME_SELECTED = OPTIONS[0]
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
