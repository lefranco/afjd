""" allgames """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, alert, document, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import mapping
import interface
import memoize
import play
import mydialog


OPTIONS = {
    'Créer une partie': "Créer une partie (pour y jouer ou l'arbitrer)",
    'Rectifier paramètres': "Rectifier un des paramètres de la partie séléctionnée",
    'Sélectionner une partie': "Séléction d'une partie sur des critères éléborés",
    'Toutes les parties': "Liste de toutes les parties",
    'Parties sans arbitre': "Liste des parties qui n'ont pas d'arbitre alloué",
    'Parties sans tournoi': "Liste des parties qui ne sont pas dans un tournoi",
    'Retourner dans la partie': "Revient dans la partie sélectionnée pour y jouer"
}

MAX_LEN_GAME_NAME = 50
MAX_LEN_VARIANT_NAME = 50

DEFAULT_SCORING_CODE = "CDIP"
DEFAULT_DEADLINE_TIME = 23
DEFAULT_GRACE_DURATION = 24
DEFAULT_SPEED_MOVES = 72
DEFAULT_SPEED_OTHERS = 24
DEFAULT_NB_CYCLES = 7

# initial deadline (in days) - how long before considering game has problems getting complete
DELAY_FOR_COMPLETING_GAME_DAYS = 21


ARRIVAL = False


def set_arrival():
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = True


def information_about_input():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= "Survolez les titres pour pour plus de détails"
    return information


def create_game(json_dict):
    """ create_game """

    # load previous values if applicable
    name = json_dict['name'] if json_dict and 'name' in json_dict else None
    variant = json_dict['variant'] if json_dict and 'variant' in json_dict else list(config.VARIANT_NAMES_DICT.keys())[0]
    fog = json_dict['fog'] if json_dict and 'fog' in json_dict else None
    exposition = json_dict['exposition'] if json_dict and 'exposition' in json_dict else None
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
    endgame_vote_allowed = json_dict['end_game_vote'] if json_dict and 'end_game_vote' in json_dict else None

    # conversion
    scoring = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[scoring_code]
    game_type = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}[game_type_code]

    # alert will be shown once
    information_displayed_disorder = False
    information_displayed_exposition = False
    information_displayed_fast = False
    information_displayed_game_type = False
    information_displayed_just_play = False
    information_displayed_deadline_time = False
    information_displayed_vote_allowed = False

    def display_disorder_callback(_):
        """ display_disorder_callback """

        nonlocal information_displayed_disorder

        if input_cd_possible_moves.checked or input_cd_possible_retreats.checked or input_cd_possible_builds.checked:
            if not information_displayed_disorder:
                alert("Attention, le désordre civil n'est pas la norme sur le site. Le remplacement des joueurs en gros retard est préconisé pour jouer des meilleures parties.\n\nDe plus, de telles parties ne devraient pas compter pour le ELO.")
                information_displayed_disorder = True

    def display_exposition_callback(_):
        """ display_exposition_callback """

        nonlocal information_displayed_exposition

        if input_exposition.checked:
            if not information_displayed_exposition:
                alert("Attention, ne cocher ce paramètre que si vous savez vraiment ce qu'il signifie. La partie est saisie par l'arbitre et destinée à être consultée par le public - ce n'est pas une partie jouée sur le site.")
                information_displayed_exposition = True

    def display_fast_callback(_):
        """ display_fast_callback """

        nonlocal information_displayed_fast

        if input_fast.checked:
            if not information_displayed_fast:
                alert("Attention, ne cocher ce paramètre que si vous savez vraiment ce qu'il signifie. La partie est jouée en temps réel (pendant plusieurs heures) comme sur un plateau en utilisant pour communiquer un logiciel de communication.")
                information_displayed_fast = True

    def display_game_type_callback(_):
        """ display_game_type_callback """

        nonlocal information_displayed_game_type

        if not information_displayed_game_type:
            all_game_types = '\n'.join(common.TYPE_GAME_EXPLAIN_CONV.values())
            avoid_open_blitz = "Attention, il est préférable d'éviter les parties BlitzOuvertes qui sont sources de tergiversations - à réserver aux parties de test !"
            explain = f"{all_game_types}\n\n{avoid_open_blitz}"
            alert(explain)
            information_displayed_game_type = True

    def display_deadline_time_callback(_):
        """ display_deadline_time_callback """

        nonlocal information_displayed_deadline_time

        if input_deadline_hour.value != DEFAULT_DEADLINE_TIME:
            if not information_displayed_deadline_time:
                alert(f"Attention, il est préférable d'éviter de dévier de l'heure des date limite 'standard' sur le site ({DEFAULT_DEADLINE_TIME}h GMT), car cela perturbe certains joueurs d'avoir des parties avec des DL différentes.")
                information_displayed_deadline_time = True

    def display_vote_allowed_callback(_):
        """ display_vote_allowed_callback """

        nonlocal information_displayed_vote_allowed

        if input_endgame_vote_allowed.checked:
            if not information_displayed_vote_allowed:
                alert("Attention, le vote de fin de partie n'a de sens que pour les parties relativement longues, c'est à dire d'au moins une dizaine d'années.")
                information_displayed_vote_allowed = True

    def display_just_play_callback(_):
        """ display_just_play_callback """

        nonlocal information_displayed_just_play

        if not information_displayed_just_play:
            alert("Si vous cochez vous serez mis dans les joueurs de la partie et le site trouvera un arbitre.\nSi vous ne cochez pas (par défaut) vous serez arbitre de la partie et ne pourrez pas la jouer.\n\nCeci est modifiable par la suite !")
            information_displayed_just_play = True

    def create_game_callback(ev):  # pylint: disable=invalid-name
        """ create_game_callback """

        nonlocal name
        nonlocal variant
        nonlocal fog
        nonlocal exposition
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
        nonlocal endgame_vote_allowed

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

            show_game_selected()

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"La partie a été créé : {messages}.")

            # we do not want stalled games
            alert(f"Attention : la partie devra être démarrée sous {DELAY_FOR_COMPLETING_GAME_DAYS} jours sous peine d'être probablement annulée.")

        ev.preventDefault()

        # get values from user input

        name = input_name.value

        # remove the number of players on the right
        variant, _, __ = input_variant.value.partition(' ')

        fog = int(input_fog.checked)
        exposition = int(input_exposition.checked)
        used_for_elo = int(input_used_for_elo.checked)
        manual = int(input_manual.checked)
        anonymous = int(input_anonymous.checked)
        fast = int(input_fast.checked)

        game_type = input_game_type.value
        scoring = input_scoring.value
        endgame_vote_allowed = int(input_endgame_vote_allowed.checked)

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
            nb_max_cycles_to_play = int(input_nb_max_cycles_to_play.value)
        except:  # noqa: E722 pylint: disable=bare-except
            nb_max_cycles_to_play = None

        # to be able to create many same games
        bypass = int(input_bypass.checked)

        # these are automatic
        time_stamp_now = time()
        time_creation = mydatetime.fromtimestamp(time_stamp_now)
        time_creation_str = mydatetime.strftime(*time_creation)

        description = f"Partie créée le {time_creation_str} par {pseudo}."
        state = 0

        # conversion
        scoring_code = config.SCORING_CODE_TABLE[scoring]
        game_type_code = config.GAME_TYPES_CODE_TABLE[game_type]

        # make data structure
        json_dict = {
            'name': name,
            'variant': variant,
            'fog': fog,
            'exposition': exposition,
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
            'nb_max_cycles_to_play': nb_max_cycles_to_play,
            'description': description,
            'current_state': state,
            'game_type': game_type_code,
            'end_vote_allowed': endgame_vote_allowed
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

        # special : check same game does not exist
        if not bypass:
            if any(g for g in games_dict.values() if all(g[vn] == json_dict[vn] for vn in ['variant', 'fog', 'fast', 'game_type'])):
                alert("Une telle partie existe déjà dans celles en attente (mêmes valeurs pour variante/brouillard/en direct/type)\nSi vous voulez malgré tout la créer, cocher la case 'Partie doublon'...")
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

    games_dict = common.get_games_data(0, 0)  # awaiting
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

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

    for variant_name, nb_players in config.VARIANT_NAMES_DICT.items():
        option = html.OPTION(f"{variant_name} ({nb_players}j.)")
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
    legend_exposition = html.LEGEND("exposition", title="ATTENTION ! Ne cocher que pour une partie pour les exposition du site - la partie n'est pas jouée - l'arbitre passe tous les ordres et tout le monde pourra en regarder le déroulement")
    fieldset <= legend_exposition
    input_exposition = html.INPUT(type="checkbox", checked=bool(exposition) if exposition is not None else False, Class='btn-inside')
    input_exposition.bind("click", display_exposition_callback)
    fieldset <= input_exposition
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

    title_endgame_vote_allowed = html.H4("Votes de fin de partie")
    form <= title_endgame_vote_allowed

    fieldset = html.FIELDSET()
    legend_endgame_vote_allowed = html.LEGEND("votes de fin", title="Les joueurs peuvent-ils voter la fin de la partie ?")
    fieldset <= legend_endgame_vote_allowed
    input_endgame_vote_allowed = html.INPUT(type="checkbox", checked=bool(endgame_vote_allowed) if endgame_vote_allowed is not None else False, Class='btn-inside')
    input_endgame_vote_allowed.bind("click", display_vote_allowed_callback)
    fieldset <= input_endgame_vote_allowed
    form <= fieldset

    title_scoring = html.H4("Système de marque")
    form <= title_scoring

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="La méthode pour compter les points (réellement pertinent pour les parties en tournoi uniquement)")
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
    legend_deadline_hour = html.LEGEND("heure de date limite (GMT)", title="Heure GMT de la journée à laquelle placer les dates limites")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="number", value=deadline_hour if deadline_hour is not None else DEFAULT_DEADLINE_TIME, Class='btn-inside')
    input_deadline_hour.bind("click", display_deadline_time_callback)
    fieldset <= input_deadline_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_sync = html.LEGEND("synchronisation des dates limites", title="Faut-il synchroniser les dates limites à une heure donnée")
    fieldset <= legend_deadline_sync
    input_deadline_sync = html.INPUT(type="checkbox", checked=bool(deadline_sync) if deadline_sync is not None else True, Class='btn-inside')
    fieldset <= input_deadline_sync
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_grace_duration = html.LEGEND("durée de grâce (heures)", title="Nombre d'heures (minutes pour une partie en direct) alloués avant fin de la grâce")
    fieldset <= legend_grace_duration
    input_grace_duration = html.INPUT(type="number", value=grace_duration if grace_duration is not None else DEFAULT_GRACE_DURATION, Class='btn-inside')
    fieldset <= input_grace_duration
    form <= fieldset

    # moves

    fieldset = html.FIELDSET()
    legend_speed_moves = html.LEGEND("cadence mouvements (heures)", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de mouvements")
    fieldset <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves if speed_moves is not None else DEFAULT_SPEED_MOVES, Class='btn-inside')
    fieldset <= input_speed_moves
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_moves = html.LEGEND("DC (Ordres par défaut pour un joueur en retard) possible mouvements", title="Désordre civil possible pour une résolution de mouvements")
    fieldset <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=bool(cd_possible_moves) if cd_possible_moves is not None else False, Class='btn-inside')
    input_cd_possible_moves.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_moves
    form <= fieldset

    # retreats

    fieldset = html.FIELDSET()
    legend_speed_retreats = html.LEGEND("cadence retraites (heures)", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite de retraites")
    fieldset <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats if speed_retreats is not None else DEFAULT_SPEED_OTHERS, Class='btn-inside')
    fieldset <= input_speed_retreats
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_cd_possible_retreats = html.LEGEND("DC (Ordres par défaut pour un joueur en retard) possible retraites", title="Désordre civil possible pour une résolution de retraites")
    fieldset <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=bool(cd_possible_retreats) if cd_possible_retreats is not None else False, Class='btn-inside')
    input_cd_possible_retreats.bind("click", display_disorder_callback)
    fieldset <= input_cd_possible_retreats
    form <= fieldset

    # adjustments

    fieldset = html.FIELDSET()
    legend_speed_adjustments = html.LEGEND("cadence ajustements (heures)", title="Nombre d'heures (minutes pour une partie en direct) alloués avant la date limite d'ajustements")
    fieldset <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments if speed_adjustments is not None else DEFAULT_SPEED_OTHERS, Class='btn-inside')
    fieldset <= input_speed_adjustments
    form <= fieldset

    # builds/removals

    fieldset = html.FIELDSET()
    legend_cd_possible_builds = html.LEGEND("DC (Ordres par défaut pour un joueur en retard) possible ajustements", title="Désordre civil possible pour une résolution d'ajustements")
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

    title_access = html.H4("Fin de la partie - ne peut plus être changé une fois la partie créée")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_nb_max_cycles_to_play = html.LEGEND("maximum de cycles (années)", title="Combien d'années à jouer au plus ?")
    fieldset <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=nb_max_cycles_to_play if nb_max_cycles_to_play is not None else DEFAULT_NB_CYCLES, Class='btn-inside')
    fieldset <= input_nb_max_cycles_to_play
    form <= fieldset

    title_access = html.H4("Spécial")
    form <= title_access

    fieldset = html.FIELDSET()
    legend_just_play_game = html.LEGEND("Je veux juste jouer la partie, pas arbitrer", title="L'administrateur du site sera mis arbitre")
    fieldset <= legend_just_play_game
    input_just_play_game = html.INPUT(type="checkbox", checked=False, Class='btn-inside')
    input_just_play_game.bind("click", display_just_play_callback)
    fieldset <= input_just_play_game
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_bypass = html.LEGEND("Partie doublon (ne pas cocher en principe)", title="Création d'une partie identique à une autre en attente")
    fieldset <= legend_bypass
    input_bypass = html.INPUT(type="checkbox", checked=False, Class='btn-inside')
    fieldset <= input_bypass
    form <= fieldset

    form <= html.BR()
    form <= html.DIV("Partie privée ? Restez arbitre, créez la partie, mettez les joueurs désirés, enlevez les non désirés si besoin et quittez l'arbitrage quand la partie est presque complète (il ne manque que vous en joueur). Un arbitre sera affecté parmi les modérateurs du site !", Class='note')
    form <= html.BR()

    input_create_game = html.INPUT(type="submit", value="Créer la partie", Class='btn-inside')
    input_create_game.bind("click", create_game_callback)
    form <= input_create_game

    MY_SUB_PANEL <= form


def rectify_parameters_game():
    """ rectify_parameters_game """

    # declare the values
    anonymity_loaded = None
    access_nopress_loaded = None
    access_nomessage_loaded = None
    description_loaded = None
    endgame_vote_allowed_loaded = None
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
            nonlocal endgame_vote_allowed_loaded
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
            endgame_vote_allowed_loaded = req_result['end_vote_allowed']
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
            mydialog.info_go(f"L'accès à l'anonymat a été modifié : {messages}")

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
            mydialog.info_go(f"L'accès à la messagerie a été modifié : {messages}")

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
            mydialog.info_go(f"La description a été modifiée : {messages}")

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

    def change_endgame_vote_allowed_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du droit a voter la fin de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du droit a voter la fin de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Le droit a voter la fin de la partie a été modifié : {messages}")

        ev.preventDefault()

        json_dict = {
            'name': game,
            'end_vote_allowed': input_endgame_vote_allowed.checked,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game endvote_allowed : need token
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
            mydialog.info_go(f"Le scorage a été modifié : {messages}")

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
            mydialog.info_go(f"Les paramètres de cadence ont été modifiés : {messages}")

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
    MY_SUB_PANEL <= html.H4("Accès à la presse et à la messagerie")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nopress = html.LEGEND("pas de presse", title="Les joueurs ne peuvent pas communiquer par presse / message *public* avant la fin de la partie")
    fieldset <= legend_nopress
    input_nopress = html.INPUT(type="checkbox", checked=access_nopress_loaded, Class='btn-inside')
    fieldset <= input_nopress
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_nomessage = html.LEGEND("pas de messagerie", title="Les joueurs ne peuvent pas communiquer par messagerie / messages  *privé* avant la fin de la partie")
    fieldset <= legend_nomessage
    input_nomessage = html.INPUT(type="checkbox", checked=access_nomessage_loaded, Class='btn-inside')
    fieldset <= input_nomessage
    form <= fieldset

    form <= html.BR()

    input_change_message_game = html.INPUT(type="submit", value="Changer l'accès à la presse et à la messagerie de la partie", Class='btn-inside')
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
    MY_SUB_PANEL <= html.H4("Votes de fin de partie")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_endgame_vote_allowed = html.LEGEND("votes de fin", title="Les joueurs peuvent-ils voter la fin de la partie ?")
    fieldset <= legend_endgame_vote_allowed
    input_endgame_vote_allowed = html.INPUT(type="checkbox", checked=endgame_vote_allowed_loaded, Class='btn-inside')
    fieldset <= input_endgame_vote_allowed
    form <= fieldset

    form <= html.BR()

    input_change_endgame_vote_allowed_game = html.INPUT(type="submit", value="Changer le droit au vote d'anonymat", Class='btn-inside')
    input_change_endgame_vote_allowed_game.bind("click", change_endgame_vote_allowed_game_callback)
    form <= input_change_endgame_vote_allowed_game

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.HR()
    MY_SUB_PANEL <= html.H4("Scorage")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="La méthode pour compter les points (réellement pertinent pour les parties en tournoi uniquement)")
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
    MY_SUB_PANEL <= html.H4("Paramètres de cadence")

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    # deadline related

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("heure de date limite (GMT)", title="Heure GMT de la journée à laquelle placer les dates limites")
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


def select_game(selected_variant, selected_state):
    """ select_game """

    def select_variant_callback(ev, input_state):  # pylint: disable=invalid-name
        """ select_game_callback """

        nonlocal selected_variant

        ev.preventDefault()

        sel_variant = input_state.value
        selected_variant = sel_variant

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    def select_state_callback(ev, input_state):  # pylint: disable=invalid-name
        """ select_state_callback """

        nonlocal selected_state

        ev.preventDefault()

        sel_state = input_state.value
        selected_state = config.STATE_CODE_TABLE[sel_state]

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    def select_game_callback(ev, input_game, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        game_name = input_game.value
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        show_game_selected()

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    games_dict = common.get_games_data(0, 3)  # all games
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    # variant selector
    # ----------------

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("Sélection de la variante", title="Sélection de la variante")
    fieldset <= legend_variant

    # list the variants we have
    variant_list = {d['variant'] for d in games_dict.values()}

    input_variant = html.SELECT(type="select-one", value="", Class='btn-inside')
    for variant in sorted(variant_list):
        option = html.OPTION(variant)
        if variant == selected_variant:
            option.selected = True
        input_variant <= option
    fieldset <= input_variant
    form <= fieldset

    input_select_variant = html.INPUT(type="submit", value="Sélectionner", Class='btn-inside')
    input_select_variant.bind("click", lambda e, i=input_variant: select_variant_callback(e, i))
    form <= input_select_variant

    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # state selector
    # ----------------

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_state = html.LEGEND("Sélection de l'état", title="Sélection de l'état")
    fieldset <= legend_state

    # list the states we have
    state_list = {d['current_state'] for d in games_dict.values()}

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    input_state = html.SELECT(type="select-one", value="", Class='btn-inside')
    for current_state in state_list:
        current_state_str = rev_state_code_table[current_state]
        option = html.OPTION(current_state_str)
        if current_state == selected_state:
            option.selected = True
        input_state <= option
    fieldset <= input_state
    form <= fieldset

    input_select_state = html.INPUT(type="submit", value="Sélectionner", Class='btn-inside')
    input_select_state.bind("click", lambda e, i=input_state: select_state_callback(e, i))
    form <= input_select_state

    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # game selector
    # ----------------

    form = html.FORM()
    fieldset = html.FIELDSET()
    legend_game = html.LEGEND("Sélection de la partie", title="Sélection de la partie")
    fieldset <= legend_game

    # list the games we have
    game_list = sorted([g['name'] for g in games_dict.values() if g['variant'] == selected_variant and g['current_state'] == selected_state], key=lambda n: n.upper())

    input_game = html.SELECT(type="select-one", value="", Class='btn-inside')
    for game in game_list:
        option = html.OPTION(game)
        if 'GAME' in storage:
            if storage['GAME'] == game:
                option.selected = True
        input_game <= option
    fieldset <= input_game
    form <= fieldset

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    input_select_game = html.INPUT(type="submit", value="Sélectionner", Class='btn-inside')
    input_select_game.bind("click", lambda e, ig=input_game, gds=game_data_sel: select_game_callback(e, ig, gds))
    form <= input_select_game

    MY_SUB_PANEL <= form


def unselect_game():
    """ unselect_game """
    if 'GAME' in storage:
        del storage['GAME']
        show_game_selected()


def show_game_selected():
    """  show_game_selected """

    log_message = html.DIV()
    if 'GAME' in storage:
        log_message <= "La partie sélectionnée est "
        log_message <= html.B(storage['GAME'])
    else:
        log_message <= "Pas de partie sélectionnée..."

    show_game_selected_panel = html.DIV(id="show_game_selected")
    show_game_selected_panel.attrs['style'] = 'text-align: left'
    show_game_selected_panel <= log_message

    if 'show_game_selected' in document:
        del document['show_game_selected']

    document <= show_game_selected_panel


def all_games(state_name):
    """all_games """

    def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def again(state_name):
        """ again """
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_ALL_GAMES']:
            storage['SORT_BY_ALL_GAMES'] = new_sort_by
            storage['REVERSE_NEEDED_ALL_GAMES'] = str(False)
        else:
            storage['REVERSE_NEEDED_ALL_GAMES'] = str(not bool(storage['REVERSE_NEEDED_ALL_GAMES'] == 'True'))

        MY_SUB_PANEL.clear()
        all_games(state_name)

    overall_time_before = time()

    # title
    title = html.H3(f"Parties dans l'état: {state_name}")
    MY_SUB_PANEL <= title

    state = config.STATE_CODE_TABLE[state_name]

    games_dict = common.get_games_data(state, state)  # in the required state
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire des joueurs")
        return

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data(state, state)  # expected state
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    masters_alloc = allocations_data['game_masters_dict']

    # fill table game -> master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            if str(game_id) in games_dict:
                game = games_dict[str(game_id)]['name']
                game_master_dict[game] = master

    time_stamp_now = time()

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

    games_table = html.TABLE()

    fields = ['name', 'id', 'deadline', 'current_advancement', 'variant', 'used_for_elo', 'master', 'nopress_current', 'nomessage_current', 'game_type']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'id': 'id', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre', 'nopress_current': 'presse', 'nomessage_current': 'messagerie', 'game_type': 'type de partie'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'deadline', 'current_advancement', 'variant', 'used_for_elo', 'master', 'nopress_current', 'nomessage_current', 'game_type']:

            if field == 'name':

                # button for sorting by creation date
                button = html.BUTTON("&lt;Date de création&gt;", Class='btn-inside')
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;Nom&gt;", Class='btn-inside')
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>", Class='btn-inside')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

        col = html.TD(buttons)
        row <= col
    games_table <= row

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if 'SORT_BY_ALL_GAMES' not in storage:
        storage['SORT_BY_ALL_GAMES'] = 'creation'
    if 'REVERSE_NEEDED_ALL_GAMES' not in storage:
        storage['REVERSE_NEEDED_ALL_GAMES'] = str(False)

    sort_by = storage['SORT_BY_ALL_GAMES']
    reverse_needed = bool(storage['REVERSE_NEEDED_ALL_GAMES'] == 'True')

    gameover_table = {int(game_id_str): data['soloed'] or data['end_voted'] or data['finished'] for game_id_str, data in games_dict.items()}

    # conversion
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_current':
        def key_function(g): return int(g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_current':
        def key_function(g): return int(g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'game_type':
        def key_function(g): return int(g[1]['game_type'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'deadline':
        def key_function(g): return int(gameover_table[int(g[0])]), int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    games_list = []

    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        if data['current_state'] != state:
            continue

        number_games += 1

        game_id = int(game_id_str)

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        # add to game list
        game_name = data['name']
        games_list.append(game_name)

        data['id'] = None
        data['master'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            arriving = False
            game_name = data['name']

            if field == 'name':
                value = game_name
                if storage['GAME_ACCESS_MODE'] == 'button':
                    button = html.BUTTON(game_name, title="Cliquer pour aller dans la partie", Class='btn-inside')
                    button.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds))
                    value = button
                else:
                    link = html.A(game_name, href=f"?game={game_name}", title="Cliquer pour aller dans la partie", target="_blank")
                    value = link

            if field == 'id':
                value = game_id

            if field == 'deadline':

                deadline_loaded = value
                datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
                value = ""

                # game over
                if gameover_table[game_id]:

                    if data['soloed']:
                        colour = config.SOLOED_COLOUR
                        value = "(solo)"
                    elif data['end_voted']:
                        colour = config.END_VOTED_COLOUR
                        value = "(fin votée)"
                    elif data['finished']:
                        colour = config.FINISHED_COLOUR
                        value = "(terminée)"

                elif int(data['current_state']) == 0:

                    value = datetime_deadline_loaded_str
                    if time_stamp_now > deadline_loaded:
                        colour = config.EXPIRED_WAIT_START_COLOUR

                elif int(data['current_state']) == 1:

                    value = datetime_deadline_loaded_str

                    # Display if forced to wait or now
                    if data['force_wait'] == 1:
                        value = html.B(f"= {value}")
                    elif data['force_wait'] == -1:
                        value = html.B(f"< {value}")

                    if data['fast']:
                        factor = 60
                    else:
                        factor = 60 * 60

                    # we are after everything !
                    if time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
                        colour = config.CRITICAL_COLOUR
                    # we are after deadline + grace
                    elif time_stamp_now > deadline_loaded + factor * data['grace_duration']:
                        colour = config.PASSED_GRACE_COLOUR
                    # we are after deadline
                    elif time_stamp_now > deadline_loaded:
                        colour = config.PASSED_DEADLINE_COLOUR
                    # deadline is today
                    elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
                        colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':
                advancement_loaded = value
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)
                if advancement_loaded > (nb_max_cycles_to_play - 1) * 5 - 1:
                    arriving = True

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            if field == 'nopress_current':
                value = "Non" if data['nopress_current'] else "Oui"

            if field == 'nomessage_current':
                value = "Non" if data['nomessage_current'] else "Oui"

            if field == 'game_type':
                if data['current_state'] in [0, 1]:
                    if not (data['soloed'] or data['end_voted'] or data['finished']):
                        # put red if incoherent
                        if value == 0:  # Nego
                            if data['nopress_current'] or data['nomessage_current']:
                                colour = 'red'
                        elif value == 1:  # Blitz
                            if not (data['nopress_current'] and data['nomessage_current']):
                                colour = 'red'
                        elif value == 2:  # Nego publique
                            if data['nopress_current'] or not data['nomessage_current']:
                                colour = 'red'
                        elif value == 3:  # Blitz ouverte
                            if data['nopress_current'] or not data['nomessage_current']:
                                colour = 'red'
                explanation = common.TYPE_GAME_EXPLAIN_CONV[value]
                stats = game_type_conv[value]
                value = html.DIV(stats, title=explanation)

            col = html.TD(value)

            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            if arriving:
                col.style = {
                    'background-color': config.LAST_YEAR
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    # store the list of games
    storage['GAME_LIST'] = ' '.join(games_list)

    overall_time_after = time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed:.2f} secs avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed / number_games:.2f} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()

    if state_name == 'en attente':
        MY_SUB_PANEL <= html.DIV("Pour les parties en attente, la date limite est pour le démarrage de la partie (pas le rendu des ordres)", Class='note')
        MY_SUB_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name, Class='btn-inside')
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))
            MY_SUB_PANEL <= input_change_state
            MY_SUB_PANEL <= "    "


def show_no_game_masters_data():
    """ show_no_game_masters_data """

    def take_mastering_this_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name

        def reply_callback(req):

            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la prise de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la prise de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                show_game_selected()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Vous avez pris l'arbitrage de la partie : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            show_no_game_masters_data()

        ev.preventDefault()

        game_id = game_data_sel[game_name][0]

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # taking game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    pseudo = None
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']

    # get the games
    games_dict = common.get_games_data(0, 3)  # all games
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data(0, 3)  # all games
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']
    games_with_master = []
    for load in masters_alloc.values():
        games_with_master += load

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    no_game_masters_table = html.TABLE()

    fields = ['game', 'take mastership']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie', 'take mastership': 'prendre l\'arbitrage'}[field]
        col = html.TD(field_fr)
        thead <= col
    no_game_masters_table <= thead

    for identifier, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        if int(identifier) in games_with_master:
            continue

        row = html.TR()

        value = data['name']
        col = html.TD(value)
        row <= col

        value = ""
        if pseudo:
            game_name = data['name']
            button = html.BUTTON("prendre", title="Cliquer pour quitter dans la partie (ne plus y jouer)", Class='btn-inside')
            button.bind("click", lambda e, gn=game_name, gds=game_data_sel: take_mastering_this_game_callback(e, gn, gds))
            value = button
        col = html.TD(value)
        row <= col

        no_game_masters_table <= row

    MY_SUB_PANEL <= html.H3("Les parties sans arbitre")
    MY_SUB_PANEL <= no_game_masters_table
    MY_SUB_PANEL <= html.BR()


def show_no_tournaments_data():
    """ show_no_tournaments_data """

    # get the games
    games_dict = common.get_games_data(0, 3)  # all games
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the groupings
    groupings_dict = common.get_groupings_data()
    if not groupings_dict:
        alert("Pas de groupements ou erreur chargement dictionnaire groupements")
        return

    games_grouped_list = sum(groupings_dict.values(), [])

    no_tournament_table = html.TABLE()

    fields = ['game', 'variant']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie', 'variant': 'variante'}[field]
        col = html.TD(field_fr)
        thead <= col
    no_tournament_table <= thead

    for identifier, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        if int(identifier) in games_grouped_list:
            continue

        row = html.TR()

        value = data['name']
        col = html.TD(value)
        row <= col

        value = data['variant']
        col = html.TD(value)
        row <= col

        no_tournament_table <= row

    MY_SUB_PANEL <= html.H3("Les parties sans tournoi")
    MY_SUB_PANEL <= no_tournament_table
    MY_SUB_PANEL <= html.BR()


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

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Créer une partie':
        create_game(None)
    if item_name == 'Rectifier paramètres':
        rectify_parameters_game()
    if item_name == 'Sélectionner une partie':
        select_game(config.FORCED_VARIANT_NAME, 1)
    if item_name == 'Toutes les parties':
        all_games('en cours')
    if item_name == 'Parties sans arbitre':
        show_no_game_masters_data()
    if item_name == 'Parties sans tournoi':
        show_no_tournaments_data()
    if item_name == 'Retourner dans la partie':
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

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


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    global ITEM_NAME_SELECTED
    global ARRIVAL

    PANEL_MIDDLE = panel_middle

    # always back to top
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0] if 'PSEUDO' in storage else list(OPTIONS.keys())[3]

    # this means user wants to edit  game
    if ARRIVAL:
        ITEM_NAME_SELECTED = 'Rectifier paramètres'
        ARRIVAL = False

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
