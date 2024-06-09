""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import mydatetime
import mydialog
import config
import common
import allgames

import index  # circular import

OPTIONS = {
    'Créer une partie': "Créer une partie (pour y jouer ou l'arbitrer)",
    'Changer anonymat': "Changer le paramètre d'anonymat sur la partie séléctionnée",
    'Changer accès messagerie': "Changer les paramètres d'acccès aux messageries sur la partie séléctionnée",
    'Changer description': "Changer la description de la partie séléctionnée",
    'Changer scorage': "Changer le paramètre système de scorage de la partie séléctionnée",
    'Changer paramètres accès': "Changer les paramètres d'accès de la partie séléctionnée",
    'Changer paramètres cadence': "Changer les paramètres de cadence la partie séléctionnée",
    'Supprimer la partie': "Supprimer la partie séléctionnée"
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


def create_game(json_dict):
    """ create_game """

    # load previous values if applicable
    name = json_dict['name'] if json_dict and 'name' in json_dict else None
    variant = json_dict['variant'] if json_dict and 'variant' in json_dict else config.VARIANT_NAMES_LIST[0]
    fog = json_dict['fog'] if json_dict and 'fog' in json_dict else None
    archive = json_dict['archive'] if json_dict and 'archive' in json_dict else None
    used_for_elo = json_dict['used_for_elo'] if json_dict and 'used_for_elo' in json_dict else None
    manual = json_dict['manual'] if json_dict and 'manual' in json_dict else None
    anonymous = json_dict['anonymous'] if json_dict and 'anonymous' in json_dict else None
    game_type_code = json_dict['game_type'] if json_dict and 'game_type' in json_dict else list(config.GAME_TYPES_CODE_TABLE.values())[0]
    fast = json_dict['fast'] if json_dict and 'fast' in json_dict else None
    scoring_code = json_dict['scoring'] if json_dict and 'scoring' in json_dict else list(config.SCORING_CODE_TABLE.values())[0]
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

    # conversion
    scoring = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[scoring_code]
    game_type = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}[game_type_code]

    # alert will be shown once
    information_displayed_disorder = False
    information_displayed_archive = False
    information_displayed_fast = False
    information_displayed_game_type = False
    information_displayed_just_play = False

    def display_disorder_callback(_):
        """ display_disorder_callback """

        nonlocal information_displayed_disorder

        if input_cd_possible_moves.checked or input_cd_possible_retreats.checked or input_cd_possible_builds.checked:
            if not information_displayed_disorder:
                alert("Attention : autoriser le Désordre Civil sur une partie (quelque soit la saison) lui enlève automatiquement l'éligibilité pour le calcul du ELO")
                information_displayed_disorder = True

    def display_archive_callback(_):
        """ display_archive_callback """

        nonlocal information_displayed_archive

        if input_archive.checked:
            if not information_displayed_archive:
                alert("Ne cochez ce paramètre que si vous savez vraiment ce qu'il signifie. La partie est saisie par l'arbitre et destinée à être consultée par le public - ce n'est pas une partie jouée sur le site")
                information_displayed_archive = True

    def display_fast_callback(_):
        """ display_fast_callback """

        nonlocal information_displayed_fast

        if input_fast.checked:
            if not information_displayed_fast:
                alert("Ne cochez ce paramètre que si vous savez vraiment ce qu'il signifie. La partie est jouée en temps réel (pendant plusieurs heures) comme sur un plateau en utilisant pour communiquer un logiciel de communication.")
                information_displayed_fast = True

    def display_game_type_callback(_):
        """ display_game_type_callback """

        nonlocal information_displayed_game_type

        if not information_displayed_game_type:
            explain = '\n'.join(common.TYPE_GAME_EXPLAIN_CONV.values())
            alert(explain)
            information_displayed_game_type = True

    def display_just_play_callback(_):
        """ display_just_play_callback """

        nonlocal information_displayed_just_play

        if not information_displayed_just_play:
            explain = '\n'.join(["Si vous cochez vous serez mis dans les joueurs de la partie et le site trouvera un arbitre", "Si vous ne cochez pas (par défaut) vous serez arbitre de la partie et ne pourrez pas la jouer", "Ceci est modifiable par la suite !"])
            alert(explain)
            information_displayed_just_play = True

    def create_game_callback(ev):  # pylint: disable=invalid-name
        """ create_game_callback """

        nonlocal name
        nonlocal variant
        nonlocal fog
        nonlocal archive
        nonlocal used_for_elo
        nonlocal manual
        nonlocal anonymous
        nonlocal game_type
        nonlocal fast
        nonlocal scoring
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

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            storage['GAME'] = name
            storage['GAME_VARIANT'] = variant

            game_id = common.get_game_id(name)
            storage['GAME_ID'] = str(game_id)

            common.info_dialog(f"Partie sélectionnée : {name} - cette information est rappelée en bas de la page")
            allgames.show_game_selected()

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La partie a été créé : {messages}")

        ev.preventDefault()

        # get values from user input

        name = input_name.value
        variant = input_variant.value
        fog = int(input_fog.checked)
        archive = int(input_archive.checked)
        used_for_elo = int(input_used_for_elo.checked)
        manual = int(input_manual.checked)
        anonymous = int(input_anonymous.checked)
        fast = int(input_fast.checked)

        game_type = input_game_type.value
        scoring = input_scoring.value

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

        # these are automatic
        time_stamp_now = time()
        time_creation = mydatetime.fromtimestamp(time_stamp_now)
        time_creation_str = mydatetime.strftime(*time_creation)

        specific_data = ""
        if fog:
            specific_data += "brouillard de guerre "
        if archive:
            specific_data += "archive "
        if manual:
            specific_data += "manuelle "
        if anonymous:
            specific_data += "anonyme "
        if fast:
            specific_data += "en direct "

        if not specific_data:
            specific_data = "(sans particularité) "

        description = f"Partie créée le {time_creation_str} par {pseudo} variante {variant}. Cette partie est {specific_data}. Type {game_type}. Scorage {scoring}."
        state = 0

        # conversion
        scoring_code = config.SCORING_CODE_TABLE[scoring]
        game_type_code = config.GAME_TYPES_CODE_TABLE[game_type]

        # make data structure
        json_dict = {
            'name': name,
            'variant': variant,
            'fog': fog,
            'archive': archive,
            'used_for_elo': used_for_elo,
            'manual': manual,
            'anonymous': anonymous,
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
            'description': description,
            'current_state': state,
            'game_type': game_type_code
        }

        just_play = int(input_just_play_game.checked)
        json_dict.update({
            'just_play': just_play
        })

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_game(json_dict)

    MY_SUB_PANEL <= html.H3("Création de partie")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    MY_SUB_PANEL <= information_about_input()

    form = html.FORM()

    legend_title_main = html.H4("Paramètres principaux de la partie - ne peuvent plus être changés une fois la partie créée")
    form <= legend_title_main

    form <= html.DIV("Pas d'accents, d'espaces ni de tirets dans le nom de la partie", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de la partie (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=name if name is not None else "", size=MAX_LEN_GAME_NAME, Class='btn-inside')
    fieldset <= input_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("variante", title="La variante de la partie")
    fieldset <= legend_variant
    input_variant = html.SELECT(type="select-one", value="", Class='btn-inside')

    for variant_name in config.VARIANT_NAMES_LIST:
        option = html.OPTION(variant_name)
        if variant_name == variant:
            option.selected = True
        input_variant <= option

    fieldset <= input_variant
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_fog = html.LEGEND("brouillard de guerre !", title="Brouillard de guerre : on ne voit que les unités voisines de ses unités et ses centres")
    fieldset <= legend_fog
    input_fog = html.INPUT(type="checkbox", checked=bool(fog) if fog is not None else False, Class='btn-inside')
    fieldset <= input_fog
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_archive = html.LEGEND("archive", title="ATTENTION ! Ne cocher que pour une partie pour les archives du site - la partie n'est pas jouée - l'arbitre passe tous les ordres et tout le monde pourra en regarder le déroulement")
    fieldset <= legend_archive
    input_archive = html.INPUT(type="checkbox", checked=bool(archive) if archive is not None else False, Class='btn-inside')
    input_archive.bind("click", display_archive_callback)
    fieldset <= input_archive
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_used_for_elo = html.LEGEND("utilisée pour le élo", title="Partie sérieuse - les résultats de la partie comptent pour le calcul du élo sur le site (forcé à faux pour les parties non standard)")
    fieldset <= legend_used_for_elo
    input_used_for_elo = html.INPUT(type="checkbox", checked=bool(used_for_elo) if used_for_elo is not None else True, Class='btn-inside')
    fieldset <= input_used_for_elo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_manual = html.LEGEND("casting manuel", title="L'arbitre attribue les rôles dans la partie et non le système")
    fieldset <= legend_manual
    input_manual = html.INPUT(type="checkbox", checked=bool(manual) if manual is not None else False, Class='btn-inside')
    fieldset <= input_manual
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_fast = html.LEGEND("en direct", title="ATTENTION ! Ne cocher que pour une partie comme sur un plateau - qui se joue en temps réel comme sur un plateau ! Le calcul des dates limites se fait en minutes au lieu d'heures.")
    fieldset <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=bool(fast) if fast is not None else False, Class='btn-inside')
    input_fast.bind("click", display_fast_callback)
    fieldset <= input_fast
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("type de partie", title="Type de partie pour la communication en jeu")
    fieldset <= legend_variant
    input_game_type = html.SELECT(type="select-one", value="", Class='btn-inside')
    input_game_type.bind("click", display_game_type_callback)

    for game_type_name in config.GAME_TYPES_CODE_TABLE:
        option = html.OPTION(game_type_name)
        if game_type_name == game_type:
            option.selected = True
        input_game_type <= option

    fieldset <= input_game_type
    form <= fieldset

    title_anonimity = html.H4("Anonymat de la partie")
    form <= title_anonimity

    fieldset = html.FIELDSET()
    legend_anonymous = html.LEGEND("anonyme", title="Les identités des joueurs ne sont pas révélées avant la fin de la partie")
    fieldset <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=bool(anonymous) if anonymous is not None else False, Class='btn-inside')
    fieldset <= input_anonymous
    form <= fieldset

    title_scoring = html.H4("Système de marque")
    form <= title_scoring

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="La méthode pour compter les points (applicable aux parties en tournoi uniquement)")
    fieldset <= legend_scoring
    input_scoring = html.SELECT(type="select-one", value="", Class='btn-inside')

    for scoring_name in config.SCORING_CODE_TABLE:
        option = html.OPTION(scoring_name)
        if scoring_name == scoring:
            option.selected = True
        input_scoring <= option

    fieldset <= input_scoring
    form <= fieldset

    title_pace = html.H4("Cadence de la partie")
    form <= title_pace

    # deadline

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("heure de date limite", title="Heure GMT de la journée à laquelle placer les dates limites")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="number", value=deadline_hour if deadline_hour is not None else DEFAULT_DEADLINE_TIME, Class='btn-inside')
    fieldset <= input_deadline_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_sync = html.LEGEND("synchronisation des dates limites", title="Faut-il synchroniser les dates limites à une heure donnée")
    fieldset <= legend_deadline_sync
    input_deadline_sync = html.INPUT(type="checkbox", checked=bool(deadline_sync) if deadline_sync is not None else True, Class='btn-inside')
    fieldset <= input_deadline_sync
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_grace_duration = html.LEGEND("durée de grâce", title="Nombre d'heures (minutes pour une partie en direct) alloués avant fin de la grâce")
    fieldset <= legend_grace_duration
    input_grace_duration = html.INPUT(type="number", value=grace_duration if grace_duration is not None else DEFAULT_GRACE_DURATION, Class='btn-inside')
    fieldset <= input_grace_duration
    form <= fieldset

    # moves

    fieldset = html.FIELDSET()
    legend_speed_moves = html.LEGEND("cadence mouvements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de mouvements")
    fieldset <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves if speed_moves is not None else DEFAULT_SPEED_MOVES, Class='btn-inside')
    fieldset <= input_speed_moves
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_moves = html.LEGEND("DC possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    fieldset <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=bool(cd_possible_moves) if cd_possible_moves is not None else False, Class='btn-inside')
    input_cd_possible_moves.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_moves
    form <= fieldset

    # retreats

    fieldset = html.FIELDSET()
    legend_speed_retreats = html.LEGEND("cadence retraites", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de retraites")
    fieldset <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats if speed_retreats is not None else DEFAULT_SPEED_OTHERS, Class='btn-inside')
    fieldset <= input_speed_retreats
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_retreats = html.LEGEND("DC possible retraites", title="Désordre civil possible pour une résolution de retraites")
    fieldset <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=bool(cd_possible_retreats) if cd_possible_retreats is not None else False, Class='btn-inside')
    input_cd_possible_retreats.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_retreats
    form <= fieldset

    # adjustments

    fieldset = html.FIELDSET()
    legend_speed_adjustments = html.LEGEND("cadence ajustements", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite d'ajustements")
    fieldset <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments if speed_adjustments is not None else DEFAULT_SPEED_OTHERS, Class='btn-inside')
    fieldset <= input_speed_adjustments
    form <= fieldset

    # builds/removals

    fieldset = html.FIELDSET()
    legend_cd_possible_builds = html.LEGEND("DC possible ajustements", title="Désordre civil possible pour une résolution d'ajustements")
    fieldset <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=bool(cd_possible_builds) if cd_possible_builds is not None else False, Class='btn-inside')
    input_cd_possible_builds.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_builds
    form <= fieldset

    # ---

    fieldset = html.FIELDSET()
    legend_play_weekend = html.LEGEND("jeu weekend", title="La date limite peut elle se trouver en fin de semaine")
    fieldset <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=bool(play_weekend) if play_weekend is not None else False, Class='btn-inside')
    fieldset <= input_play_weekend
    form <= fieldset

    title_access = html.H4("Accès à la partie - ne peuvent plus être changés une fois la partie démarrée")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_access_restriction_reliability = html.LEGEND("restriction fiabilité", title="Sélectionne les joueurs sur leur fiabilité")
    fieldset <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability if access_restriction_reliability is not None else "", Class='btn-inside')
    fieldset <= input_access_restriction_reliability
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_regularity = html.LEGEND("restriction régularité", title="Sélectionne les joueurs sur leur régularité")
    fieldset <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity if access_restriction_regularity is not None else "", Class='btn-inside')
    fieldset <= input_access_restriction_regularity
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_access_restriction_performance = html.LEGEND("restriction performance", title="Sélectionne les joueurs sur leur niveau de performance")
    fieldset <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance if access_restriction_performance is not None else "", Class='btn-inside')
    fieldset <= input_access_restriction_performance
    form <= fieldset

    title_access = html.H4("Fin de la partie - ne peut plus être changé une fois la partie créée")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_nb_max_cycles_to_play = html.LEGEND("maximum de cycles (années)", title="Combien d'années à jouer au plus ?")
    fieldset <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=nb_max_cycles_to_play if nb_max_cycles_to_play is not None else DEFAULT_NB_CYCLES, Class='btn-inside')
    fieldset <= input_nb_max_cycles_to_play
    form <= fieldset

    title_access = html.H4("Spécial : rôle du créateur dans la partie")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_just_play_game = html.LEGEND("Je veux juste jouer la partie", title="L'administrateur du site sera mis arbitre")
    fieldset <= legend_just_play_game
    input_just_play_game = html.INPUT(type="checkbox", checked=False, Class='btn-inside')
    input_just_play_game.bind("click", display_just_play_callback)
    fieldset <= input_just_play_game
    form <= fieldset

    form <= html.BR()

    input_create_game = html.INPUT(type="submit", value="Créer la partie", Class='btn-inside')
    input_create_game.bind("click", create_game_callback)
    form <= input_create_game

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

        # changing game scoring : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    status = change_anonymity_reload()
    if not status:
        return

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
            req_result = loads(req.text)

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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

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
        change_access_messages_game()

    MY_SUB_PANEL <= html.H3("Changement de l'accès aux messagerie")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    status = change_access_messages_reload()
    if not status:
        return

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
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

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
        change_description_game()

    MY_SUB_PANEL <= html.H3("Changement de la description")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

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

    input_change_description_game = html.INPUT(type="submit", value="Changer la description de la partie", Class='btn-inside')
    input_change_description_game.bind("click", change_description_game_callback)
    form <= input_change_description_game

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
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

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
        change_scoring_game()

    MY_SUB_PANEL <= html.H3("Changement du scorage")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    status = change_scoring_reload()
    if not status:
        return

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
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

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
        change_access_parameters_game()

    MY_SUB_PANEL <= html.H3("Changement des paramètres d'accès")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    status = change_access_parameters_reload()
    if not status:
        return

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


def change_pace_parameters_game():
    """ change_pace_parameters_game """

    information_displayed_disorder = False

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

    def display_disorder_callback(_):
        """ display_disorder_callback """

        nonlocal information_displayed_disorder

        if input_cd_possible_moves.checked or input_cd_possible_retreats.checked or input_cd_possible_builds.checked:
            if not information_displayed_disorder:
                alert("Attention : autoriser le Désordre Civil sur une partie (quelque soit la saison) lui enlève automatiquement l'éligibilité pour le calcul du ELO")
                information_displayed_disorder = True

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
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

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
        change_pace_parameters_game()

    MY_SUB_PANEL <= html.H3("Changement de paramètres de cadence")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

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


def delete_game():
    """ delete_game """

    def cancel_delete_game_callback(_, dialog):
        """ cancel_delete_game_callback """
        dialog.close(None)

    def delete_game_callback(ev, dialog):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La partie a été supprimée : {messages}")
            allgames.unselect_game()

            # go to select another game
            index.load_option(None, 'Sélectionner partie')

        ev.preventDefault()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # deleting game : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_game_callback_confirm(ev):  # pylint: disable=invalid-name
        """ delete_game_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On supprime vraiment la partie {game} ?", ok_cancel=True)
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

    form = html.FORM()

    input_delete_game = html.INPUT(type="submit", value="Supprimer la partie", Class='btn-inside')
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

MY_SUB_PANEL = html.DIV(id="page")
MY_PANEL <= MY_SUB_PANEL


ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]


def load_option(_, item_name):
    """ load_option """

    global ITEM_NAME_SELECTED

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Créer une partie':
        create_game(None)
    if item_name == 'Changer anonymat':
        change_anonymity_game()
    if item_name == 'Changer accès messagerie':
        change_access_messages_game()
    if item_name == 'Changer description':
        change_description_game()
    if item_name == 'Changer scorage':
        change_scoring_game()
    if item_name == 'Changer paramètres accès':
        change_access_parameters_game()
    if item_name == 'Changer paramètres cadence':
        change_pace_parameters_game()
    if item_name == 'Supprimer la partie':
        delete_game()

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
