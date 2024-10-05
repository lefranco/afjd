""" players """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from math import exp

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import interface
import config
import mapping
import mydialog
import scoring
import ezml_render


DEFAULT_ELO = 1500


OPTIONS = {
    'Classement performance': "Classement selon la performance, c'est à dire le E.L.O.",
    'Classement fiabilité': "Classement selon la fiabilité, c'est à dire pas de retard ni d'abandon",
    'Classement régularité': "Classement selon la régularité, c'est à dire jouer souvent et sans interruption",
    'Les glorieux': "Les joueurs du site qui ont un titre en face à face",
    'Liste globale': "Les joueurs et arbitres sur le site",
    'Les scorages': "Les systèmes de scorage disponibles  sur le site"
}

ARRIVAL = False

# from home
SCORING_REQUESTED = list(config.SCORING_CODE_TABLE.values())[0]


def set_arrival(scoring_requested):
    """ set_arrival """

    global ARRIVAL
    global SCORING_REQUESTED

    ARRIVAL = True
    SCORING_REQUESTED = scoring_requested


def show_games(ev, game_list):  # pylint: disable=invalid-name
    """ show_games """
    ev.preventDefault()
    mydialog.InfoDialog("Information", game_list, True)


def get_detailed_elo_rating(classic, role_id):
    """ get_detailed_elo_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement ELO détaillé : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement ELO détaillé : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating/{int(classic)}/{role_id}"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_global_elo_rating(classic):
    """ get_global_elo_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement ELO  global : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement ELO global : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating/{int(classic)}"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_reliability_rating():
    """ get_reliability_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement fiabilité : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement fiabilité : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/reliability_rating"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_regularity_rating():
    """ get_regularity_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement regularité : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement regularité : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/regularity_rating"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def show_rating_performance(classic, role_id):
    """ show_rating_performance """

    def make_ratings_table(classic, role_id, nb_roles):

        if role_id:

            # for a given role
            rating_list = get_detailed_elo_rating(classic, role_id)

        else:

            # for all roles
            complete_rating_list = get_global_elo_rating(classic)

            # need to sum up per player
            rating_list_dict = {}
            for (classic2, role_id2, player_id, elo, change, game_id, number_games) in complete_rating_list:

                # avoid using loop variable
                classic_found = classic2

                # create entry if necessary
                if player_id not in rating_list_dict:
                    rating_list_dict[player_id] = {}
                    rating_list_dict[player_id]['elo_sum'] = 0
                    rating_list_dict[player_id]['number_games'] = 0
                    rating_list_dict[player_id]['number_rated'] = 0

                # update entry

                # suming up
                rating_list_dict[player_id]['elo_sum'] += elo
                rating_list_dict[player_id]['number_games'] += number_games
                rating_list_dict[player_id]['number_rated'] += 1

                # last
                rating_list_dict[player_id]['last_change'] = change
                rating_list_dict[player_id]['last_game'] = game_id
                rating_list_dict[player_id]['last_role'] = role_id2

            rating_list = [[classic_found, v['last_role'], k, round((v['elo_sum'] + (nb_roles - v['number_rated']) * DEFAULT_ELO) / nb_roles), v['last_change'], v['last_game'], v['number_games']] for k, v in rating_list_dict.items()]

        ratings_table = html.TABLE()

        # the display order
        fields = ['rank', 'player', 'elo', 'change', 'role', 'game', 'number']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'rank': 'rang', 'player': 'joueur', 'elo': 'elo', 'change': 'dernier changement', 'role': 'avec le rôle', 'game': 'dans la partie', 'number': 'nombre de parties'}[field]
            col = html.TD(field_fr)
            thead <= col
        ratings_table <= thead

        row = html.TR()
        for field in fields:
            buttons = html.DIV()
            if field in ['player', 'elo', 'change', 'role', 'game', 'number']:

                # button for sorting
                button = html.BUTTON("<>", Class='btn-inside')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_ELO_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_ELO_RATINGS'] == 'True')

        # 0 classic / 1 role_id / 2 player_id / 3 elo / 4 change / 5 game_id / 6 number games

        if sort_by == 'player':
            def key_function(r): return num2pseudo[r[2]].upper() if r[2] in num2pseudo else ""  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'elo':
            def key_function(r): return r[3]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'change':
            def key_function(r): return r[4]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'role':
            def key_function(r): return r[1]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'game':
            def key_function(r): return games_dict[str(r[5])]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number':
            def key_function(r): return r[6]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

        elo_sorted = sorted(rating_list, key=lambda r: r[3], reverse=True)
        rank_table = {p[2]: i + 1 for i, p in enumerate(elo_sorted)}

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[2]] if rating[2] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank_table[rating[2]]

                if field == 'player':
                    value = player

                if field == 'elo':
                    value = rating[3]

                if field == 'change':
                    value = f"{round(rating[4] / nb_roles):+} ({rating[4]:+})"

                if field == 'role':
                    role_id = rating[1]
                    role = variant_data.roles[role_id]
                    role_name = variant_data.role_name_table[role]
                    role_icon_img = common.display_flag(variant_name, interface_chosen, role_id, role_name)
                    value = role_icon_img

                if field == 'game':
                    value = games_dict[str(rating[5])]['name'] if str(rating[5]) in games_dict else ""

                if field == 'number':
                    value = rating[6]

                col = html.TD(value)
                if colour is not None:
                    col.style = {
                        'background-color': colour
                    }

                row <= col

            ratings_table <= row

        average = round(sum(r[3] for r in rating_list) / len(rating_list))
        return ratings_table, average

    def refresh():

        # should be 7
        nb_roles = len(variant_data.roles) - 1

        ratings_table, average = make_ratings_table(classic, role_id, nb_roles)

        # button for changing mode
        switch_mode_button = html.BUTTON(f"Passer en {'blitz' if classic else 'classique'}", Class='btn-inside')
        switch_mode_button.bind("click", switch_mode_callback)

        # button for going global
        switch_global_button = html.BUTTON("Classement global", Class='btn-inside')
        switch_global_button.bind("click", lambda e: switch_role_callback(e, None))

        # buttons for selecting role
        switch_role_buttons_table = html.TABLE()
        row = html.TR()
        col = html.TD("Cliquer sur le pays pour le détail ->")
        row <= col
        for poss_role_id, poss_role in variant_data.roles.items():
            if poss_role_id >= 1 and poss_role_id != role_id:
                form = html.FORM()
                role_name = variant_data.role_name_table[poss_role]
                role_icon_img = common.display_flag(variant_name, interface_chosen, poss_role_id, role_name)
                role_icon_img.bind("click", lambda e, r=poss_role_id: switch_role_callback(e, r))
                form <= role_icon_img
                col = html.TD(form)
                row <= col
        switch_role_buttons_table <= row

        MY_SUB_PANEL.clear()
        MY_SUB_PANEL <= html.H3("Le classement par performance")
        MY_SUB_PANEL <= html.DIV("Ce classement est un ELO - il prend en compte le résultat des joueurs sur les parties par rapport aux autres", Class='important')
        MY_SUB_PANEL <= html.DIV(f"Mode de jeu sélectionné {'classique' if classic else 'blitz'}")
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= switch_mode_button
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()
        if role_id:
            MY_SUB_PANEL <= switch_global_button
            MY_SUB_PANEL <= html.BR()
            MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= switch_role_buttons_table
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= ratings_table
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV(f"La moyenne des ELO est de {average}", Class='note')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("Le changement indiqué est celui global pour le joueur, celui entre parenthèse pour le rôle donné.", Class='note')

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by is not None:
            if new_sort_by != storage['SORT_BY_ELO_RATINGS']:
                storage['SORT_BY_ELO_RATINGS'] = new_sort_by
                storage['REVERSE_NEEDED_ELO_RATINGS'] = str(True)
            else:
                storage['REVERSE_NEEDED_ELO_RATINGS'] = str(not bool(storage['REVERSE_NEEDED_ELO_RATINGS'] == 'True'))

        refresh()

    def switch_mode_callback(_):

        # note : actualy 'classic' is a parameter, not a variable
        nonlocal classic
        classic = not classic
        refresh()

    def switch_role_callback(_, new_role_id):

        # note : actualy 'role_id' is a parameter, not a variable
        nonlocal role_id
        role_id = new_role_id
        refresh()

    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']
    else:
        pseudo = None

    variant_name = config.FORCED_VARIANT_NAME

    variant_content = common.game_variant_content_reload(variant_name)
    interface_chosen = interface.get_interface_from_variant(variant_name)
    interface_parameters = common.read_parameters(variant_name, interface_chosen)

    variant_data = mapping.Variant(variant_name, variant_content, interface_parameters)

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    # default
    if 'SORT_BY_ELO_RATINGS' not in storage:
        storage['SORT_BY_ELO_RATINGS'] = 'elo'
    if 'REVERSE_NEEDED_ELO_RATINGS' not in storage:
        storage['REVERSE_NEEDED_ELO_RATINGS'] = str(True)

    sort_by_callback(None, None)


def show_rating_reliability():
    """ show_rating_reliability """

    def make_ratings_table():

        # get data
        complete_rating_list = get_reliability_rating()

        # from raw data to displayable data (simpler than ELO here)
        rating_list = []
        for player_id, number_delays, number_dropouts, number_advancements in complete_rating_list:

            # verdict - mostly a ratio
            # avoid division by zero
            if number_advancements == 0:
                number_advancements = 1
            # ratio
            reliability = round(100 * (number_advancements - number_delays) / number_advancements, 3)
            # bonus for no delays
            if number_delays == 0:
                reliability += number_advancements / 1000
            # dropouts
            reliability /= 2 ** number_dropouts

            rating = (player_id, reliability, number_delays, number_dropouts, number_advancements)
            rating_list.append(rating)

        ratings_table = html.TABLE()

        # the display order
        fields = ['rank', 'player', 'reliability', 'number_delays', 'number_dropouts', 'number']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'rank': 'rang', 'player': 'joueur', 'reliability': 'fiabilité', 'number_delays': 'nombre de retards', 'number_dropouts': 'nombre d\'abandons', 'number': 'nombre de tours joués'}[field]
            col = html.TD(field_fr)
            thead <= col
        ratings_table <= thead

        row = html.TR()
        for field in fields:
            buttons = html.DIV()
            if field in ['player', 'reliability', 'number_delays', 'number_dropouts', 'number']:

                # button for sorting
                button = html.BUTTON("<>", Class='btn-inside')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_REL_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_REL_RATINGS'] == 'True')

        # 0 player_id / 1 reliability / 2 number_delays/ 3 number_dropouts / 4 non_obsolescence / 5 number advancements

        if sort_by == 'player':
            def key_function(r): return num2pseudo[r[0]].upper() if r[0] in num2pseudo else ""  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'reliability':
            def key_function(r): return r[1]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number_delays':
            def key_function(r): return r[2]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number_dropouts':
            def key_function(r): return r[3]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number':
            def key_function(r): return r[4]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

        reliability_sorted = sorted(rating_list, key=lambda r: r[1], reverse=True)
        rank_table = {p[0]: i + 1 for i, p in enumerate(reliability_sorted)}

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[0]] if rating[0] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank_table[rating[0]]

                if field == 'player':
                    value = player

                if field == 'reliability':
                    value = f"{rating[1]} %"

                if field == 'number_delays':
                    value = rating[2]

                if field == 'number_dropouts':
                    value = rating[3]

                if field == 'number':
                    value = rating[4]

                col = html.TD(value)
                if colour is not None:
                    col.style = {
                        'background-color': colour
                    }

                row <= col

            ratings_table <= row

        return ratings_table

    def refresh():

        ratings_table = make_ratings_table()

        MY_SUB_PANEL.clear()
        MY_SUB_PANEL <= html.H3("Le classement par fiabilité")
        MY_SUB_PANEL <= html.DIV("Ce classement est un ratio du nombre de tours joués moins le nombre de retards par rapport au nombre de tours joués. Les joueurs sans retard sont bonifiés du millième du nombre de tours joués. Chaque abandon divise par deux la fiabilité. Seuls les joueurs présents à la fin de la partie ont joué la partie. Un joueur qui n'a joué aucune partie (présent parce qu'il a tout de même un retard ou un abandon) reçoit un tour joué.", Class='important')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= ratings_table
        MY_SUB_PANEL <= html.BR()

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by is not None:
            if new_sort_by != storage['SORT_BY_REL_RATINGS']:
                storage['SORT_BY_REL_RATINGS'] = new_sort_by
                storage['REVERSE_NEEDED_REL_RATINGS'] = str(True)
            else:
                storage['REVERSE_NEEDED_REL_RATINGS'] = str(not bool(storage['REVERSE_NEEDED_REL_RATINGS'] == 'True'))

        refresh()

    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']
    else:
        pseudo = None

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # default
    if 'SORT_BY_REL_RATINGS' not in storage:
        storage['SORT_BY_REL_RATINGS'] = 'reliability'
    if 'REVERSE_NEEDED_REL_RATINGS' not in storage:
        storage['REVERSE_NEEDED_REL_RATINGS'] = str(True)

    sort_by_callback(None, None)


def show_rating_regularity():
    """ show_rating_regularity """

    def make_ratings_table():

        # get data
        complete_rating_list = get_regularity_rating()

        # from raw data to displayable data (simpler than ELO here)
        rating_list = []
        for player_id, started_playing_days, finished_playing_days, activity_days, number_games in complete_rating_list:

            # for how long been playing (in weeks)
            seniority = round(started_playing_days / 7)

            # how recent is the activity - that is a ratio
            non_obsolescence = round(exp(- finished_playing_days / 365.2), 3)

            # how continuous (there must a few gaps as possible)
            play_duration = max(started_playing_days - finished_playing_days, 0.5)
            continuity = round(100 * max(activity_days, 0.5) / play_duration, 2)

            # verdict - just a product
            regularity = round(seniority * non_obsolescence * continuity * number_games / 100, 2)

            rating = (player_id, regularity, seniority, non_obsolescence, continuity, number_games)
            rating_list.append(rating)

        ratings_table = html.TABLE()

        # the display order
        fields = ['rank', 'player', 'regularity', 'seniority', 'non_obsolescence', 'continuity', 'number']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'rank': 'rang', 'player': 'joueur', 'regularity': 'régularité', 'seniority': 'ancienneté', 'non_obsolescence': 'non obsolescence', 'continuity': 'continuité', 'number': 'nombre de parties'}[field]
            col = html.TD(field_fr)
            thead <= col
        ratings_table <= thead

        row = html.TR()
        for field in fields:
            buttons = html.DIV()
            if field in ['player', 'regularity', 'seniority', 'non_obsolescence', 'continuity', 'number']:

                # button for sorting
                button = html.BUTTON("<>", Class='btn-inside')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_REG_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_REG_RATINGS'] == 'True')

        # 0 player_id / 1 regularity / 2 seniority/ 3 non_obsolescence / 4 continuity / 5 number games

        if sort_by == 'player':
            def key_function(r): return num2pseudo[r[0]].upper() if r[0] in num2pseudo else ""  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'regularity':
            def key_function(r): return r[1]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'seniority':
            def key_function(r): return r[2]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'non_obsolescence':
            def key_function(r): return r[3]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'continuity':
            def key_function(r): return r[4]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number':
            def key_function(r): return r[5]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

        regularity_sorted = sorted(rating_list, key=lambda r: r[1], reverse=True)
        rank_table = {p[0]: i + 1 for i, p in enumerate(regularity_sorted)}

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[0]] if rating[0] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank_table[rating[0]]

                if field == 'player':
                    value = player

                if field == 'regularity':
                    value = rating[1]

                if field == 'seniority':
                    value = rating[2]

                if field == 'non_obsolescence':
                    value = rating[3]

                if field == 'continuity':
                    value = f"{rating[4]} %"

                if field == 'number':
                    value = rating[5]

                col = html.TD(value)
                if colour is not None:
                    col.style = {
                        'background-color': colour
                    }

                row <= col

            ratings_table <= row

        return ratings_table

    def refresh():

        ratings_table = make_ratings_table()

        MY_SUB_PANEL.clear()
        MY_SUB_PANEL <= html.H3("Le classement par régularité")
        MY_SUB_PANEL <= html.DIV("Ce classement est une aggrégation par produit de l'ancienneté, la non obsolescence, la continuité et le nombre de parties", Class='important')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= ratings_table
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("L'ancienneté est le nombre de semaines écoulées depuis le début de la première partie jouée (pour favoriser les joueurs qui ont commencé il y a longtemps)", Class='note')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("La non obsolecence est égale à l'exponentielle de moins le nombre d'années écoulées depuis la fin de la dernière partie jouée (pour favoriser les joueurs qui jouent encore maintenant)", Class='note')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("La continuité est la proportion de jours actifs (dans une partie en cours) entre le début de la première partie et la fin de la dernière partie (pour favoriser les joueurs qui jouent sans s'arrêter)", Class='note')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("Le nombre de parties se passe d'explications (pour favoriser les joueurs qui jouent le plus de parties)", Class='note')

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by is not None:
            if new_sort_by != storage['SORT_BY_REG_RATINGS']:
                storage['SORT_BY_REG_RATINGS'] = new_sort_by
                storage['REVERSE_NEEDED_REG_RATINGS'] = str(True)
            else:
                storage['REVERSE_NEEDED_REG_RATINGS'] = str(not bool(storage['REVERSE_NEEDED_REG_RATINGS'] == 'True'))

        refresh()

    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']
    else:
        pseudo = None

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # default
    if 'SORT_BY_REG_RATINGS' not in storage:
        storage['SORT_BY_REG_RATINGS'] = 'regularity'
    if 'REVERSE_NEEDED_REG_RATINGS' not in storage:
        storage['REVERSE_NEEDED_REG_RATINGS'] = str(True)

    sort_by_callback(None, None)


def show_glorious_data():
    """ show_glorious_data """

    news_content_table_loaded = common.get_news_content()
    hall_content_loaded = news_content_table_loaded['glory']
    hall_content = common.formatted_news(hall_content_loaded, None, 'glory_news')

    MY_SUB_PANEL <= html.H3("Les glorieux")
    MY_SUB_PANEL <= hall_content


def show_players_masters_data():
    """ show_players_masters_data """

    priviledged = common.PRIVILEDGED
    if not priviledged:
        return

    creators_list = priviledged['creators']
    moderators_list = priviledged['moderators']
    admin_pseudo = priviledged['admin']

    # get the games
    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    # get the players
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    # get the link (allocations) of players for ongoing games
    state = 1
    allocations_data_ongoing = common.get_allocations_data(state)
    if not allocations_data_ongoing:
        alert("Erreur chargement allocations en cours")
        return

    active_dict = allocations_data_ongoing['active_dict']
    player_activity_dict = {}
    for player_id, number in active_dict.items():
        player = players_dict[str(player_id)]['pseudo']
        player_activity_dict[player] = number

    # gather games to players ongoing
    players_alloc_ongoing = allocations_data_ongoing['players_dict']
    player_games_ongoing_dict = {}
    for player_id, games_id in players_alloc_ongoing.items():
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_ongoing_dict:
            player_games_ongoing_dict[player] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_ongoing_dict[player].append(game)

    # gather games to players
    players_alloc = allocations_data['players_dict']
    player_games_dict = {}
    for player_id, games_id in players_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    # others
    player_others_dict = {player: sorted(set(all_games) - set(player_games_ongoing_dict.get(player, []))) for player, all_games in player_games_dict.items()}

    # gather games to masters
    masters_alloc = allocations_data['game_masters_dict']
    master_games_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        if master not in master_games_dict:
            master_games_dict[master] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            master_games_dict[master].append(game)

    players_masters_table = html.TABLE()

    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone', 'activity', 'ongoing_played_games', 'other_played_games', 'mastered_games', 'replaces', 'site_roles']

    # header

    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire', 'activity': 'activité', 'ongoing_played_games': 'parties en cours', 'other_played_games': 'parties terminées, en attente ou distinguées', 'mastered_games': 'parties arbitrées', 'replaces': 'remplaçant', 'site_roles': 'rôles sur le site'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_masters_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    count1 = 0
    count2 = 0
    count3 = 0
    count4 = 0

    for data in sorted(players_dict.values(), key=lambda g: g['pseudo'].upper()):
        row = html.TR()

        data['activity'] = None
        data['ongoing_played_games'] = None
        data['other_played_games'] = None
        data['mastered_games'] = None
        data['replaces'] = None
        data['site_roles'] = None

        for field in fields:

            value = data[field]

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            if field == 'activity':
                value = ""
                player = data['pseudo']
                if player in player_activity_dict:
                    value = player_activity_dict[player]
                    count2 += 1

            if field == 'ongoing_played_games':
                player = data['pseudo']
                games = player_games_ongoing_dict.get(player, [])
                value = ""
                if games:
                    nb_games = len(games)
                    button = html.BUTTON(f"Voir les {nb_games} partie(s)", title="Voir", Class='btn-menu')
                    games_list = ' '.join(sorted(games))
                    button.bind("click", lambda e, gl=games_list: show_games(e, gl))
                    value = button

            if field == 'other_played_games':
                player = data['pseudo']
                games = player_others_dict.get(player, [])
                value = ""
                if games:
                    nb_games = len(games)
                    button = html.BUTTON(f"Voir les {nb_games} partie(s)", title="Voir", Class='btn-menu')
                    games_list = ' '.join(sorted(games))
                    button.bind("click", lambda e, gl=games_list: show_games(e, gl))
                    value = button

            if field == 'mastered_games':
                player = data['pseudo']
                games = master_games_dict.get(player, [])
                value = ""
                if games:
                    nb_games = len(games)
                    button = html.BUTTON(f"Voir les {nb_games} partie(s)", title="Voir", Class='btn-menu')
                    games_list = ' '.join(sorted(games))
                    button.bind("click", lambda e, gl=games_list: show_games(e, gl))
                    value = button
                    count3 += 1

            if field == 'replaces':
                value = ""
                if data['notify_replace']:
                    value = "oui"
                    count4 += 1

            if field == 'site_roles':
                value = ""
                if data['pseudo'] in creators_list:
                    value += "créateur "
                if data['pseudo'] in moderators_list:
                    value += "modérateur "
                if data['pseudo'] == admin_pseudo:
                    value += "administrateur "

            col = html.TD(value)
            row <= col

        players_masters_table <= row
        count1 += 1

    MY_SUB_PANEL <= html.H3("Les joueurs, arbitres et remplaçants et les rôles")
    MY_SUB_PANEL <= html.DIV("Les joueurs dans des parties anonymes ne sont pas pris en compte (sauf pour 'activité' qui compte les parties jouées en cours)", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= players_masters_table
    MY_SUB_PANEL <= html.P(f"Il y a {count1} inscrits dont {count2} joueurs actifs et {count3} arbitres pour {count4} remplaçants potentiels.")


RATING_TABLE = {}


def show_scoring():
    """ show_scoring """

    def change_scoring_callback(ev):  # pylint: disable=invalid-name
        """ change_scoring_callback """

        global SCORING_REQUESTED

        ev.preventDefault()

        # Change scoring selected
        scoring1 = input_scoring.value
        SCORING_REQUESTED = config.SCORING_CODE_TABLE[scoring1]

        # back to where we started
        MY_SUB_PANEL.clear()
        show_scoring()

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

        # must be sorted
        rating_table = dict(sorted(RATING_TABLE.items(), key=lambda i: i[1], reverse=True))

        # scoring
        centers_variant = variant_data.number_centers()
        score_table = scoring.scoring(SCORING_REQUESTED, centers_variant, rating_table)

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

    title = html.H3("Test du scorage")
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

    information = html.DIV(Class='important')
    information <= "Pour se placer dans une autre variante, sélectionner une partie de cette variante au préalable."
    MY_SUB_PANEL <= information

    MY_SUB_PANEL <= html.H4("Entrer les nombre de centres")

    form = html.FORM()

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

    input_test_scoring = html.INPUT(type="submit", value="Calculer la marque avec ce scorage", Class='btn-inside')
    input_test_scoring.bind("click", lambda e, ri=ratings_input: test_scoring_callback(e, ri))
    form <= input_test_scoring

    MY_SUB_PANEL <= form

    title = html.H3("Changement de scorage")
    MY_SUB_PANEL <= title

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_scoring = html.LEGEND("scorage", title="Le scorage à étudier")
    fieldset <= legend_scoring
    input_scoring = html.SELECT(type="select-one", value="", Class='btn-inside')

    for scoring_name in config.SCORING_CODE_TABLE:
        option = html.OPTION(scoring_name)
        if config.SCORING_CODE_TABLE[scoring_name] == SCORING_REQUESTED:
            option.selected = True
        input_scoring <= option
    fieldset <= input_scoring
    form <= fieldset

    input_select_scoring = html.INPUT(type="submit", value="Sélectionner ce scorage", Class='btn-inside')
    input_select_scoring.bind("click", change_scoring_callback)
    form <= input_select_scoring

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

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="page")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Classement performance':
        show_rating_performance(True, None)
    if item_name == 'Classement fiabilité':
        show_rating_reliability()
    if item_name == 'Classement régularité':
        show_rating_regularity()
    if item_name == 'Les glorieux':
        show_glorious_data()
    if item_name == 'Liste globale':
        show_players_masters_data()
    if item_name == 'Les scorages':
        show_scoring()

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

    # this means user wants to see scoring
    if ARRIVAL:
        ITEM_NAME_SELECTED = 'Les scorages'
        ARRIVAL = False

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
