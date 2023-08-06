""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import math

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import interface
import config
import mapping

DEFAULT_ELO = 1500


OPTIONS = ['Classement performance', 'Classement fiabilité', 'Classement régularité', 'Liste inscrits', 'Liste joueurs', 'Liste arbitres', 'Abonnés remplaçants', 'Groupe créateurs', 'Groupe modérateurs']


def get_detailed_elo_rating(classic, role_id):
    """ get_detailed_elo_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_global_elo_rating(classic):
    """ get_global_elo_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_reliability_rating():
    """ get_reliability_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_regularity_rating():
    """ get_regularity_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
                button = html.BUTTON("<>", Class='btn-menu')
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

        rank = 1

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[2]] if rating[2] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank

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
                    role_icon_img = html.IMG(src=f"./variants/{variant_name}/{interface_chosen}/roles/{role_id}.jpg", title=role_name)
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
            rank += 1

        average = round(sum(r[3] for r in rating_list) / len(rating_list))
        return ratings_table, average

    def refresh():

        # should be 7
        nb_roles = len(variant_data.roles) - 1

        ratings_table, average = make_ratings_table(classic, role_id, nb_roles)

        # button for changing mode
        switch_mode_button = html.BUTTON(f"Passer en {'blitz' if classic else 'classique'}", Class='btn-menu')
        switch_mode_button.bind("click", switch_mode_callback)

        # button for going global
        switch_global_button = html.BUTTON("Classement global", Class='btn-menu')
        switch_global_button.bind("click", lambda e: switch_role_callback(e, None))

        # buttons for selecting role
        switch_role_buttons_table = html.TABLE()
        row = html.TR()
        col = html.TD("Cliquer sur le pays pour le détail ->")
        row <= col
        for poss_role_id in variant_data.roles:
            if poss_role_id >= 1 and poss_role_id != role_id:
                form = html.FORM()
                input_change_role = html.INPUT(type="image", src=f"./variants/{variant_name}/{interface_chosen}/roles/{poss_role_id}.jpg")
                input_change_role.bind("click", lambda e, r=poss_role_id: switch_role_callback(e, r))
                form <= input_change_role
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
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

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
                button = html.BUTTON("<>", Class='btn-menu')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_REL_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_REL_RATINGS'] == 'True')

        # 0 player_id / 1 reliability / 2 number_delays/ 3 number_dropouts / 4 non_obsolesence / 5 number advancements

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

        rank = 1

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[0]] if rating[0] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank

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
            rank += 1

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
            non_obsolesence = round(math.exp(- finished_playing_days / 365.2), 3)

            # how continuous (there must a few gaps as possible)
            play_duration = max(started_playing_days - finished_playing_days, 0.5)
            continuity = round(100 * max(activity_days, 0.5) / play_duration, 2)

            # verdict - just a product
            regularity = round(seniority * non_obsolesence * continuity * number_games / 100, 2)

            rating = (player_id, regularity, seniority, non_obsolesence, continuity, number_games)
            rating_list.append(rating)

        ratings_table = html.TABLE()

        # the display order
        fields = ['rank', 'player', 'regularity', 'seniority', 'non_obsolesence', 'continuity', 'number']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'rank': 'rang', 'player': 'joueur', 'regularity': 'régularité', 'seniority': 'ancienneté', 'non_obsolesence': 'non obsolesence', 'continuity': 'continuité', 'number': 'nombre de parties'}[field]
            col = html.TD(field_fr)
            thead <= col
        ratings_table <= thead

        row = html.TR()
        for field in fields:
            buttons = html.DIV()
            if field in ['player', 'regularity', 'seniority', 'non_obsolesence', 'continuity', 'number']:

                # button for sorting
                button = html.BUTTON("<>", Class='btn-menu')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_REG_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_REG_RATINGS'] == 'True')

        # 0 player_id / 1 regularity / 2 seniority/ 3 non_obsolesence / 4 continuity / 5 number games

        if sort_by == 'player':
            def key_function(r): return num2pseudo[r[0]].upper() if r[0] in num2pseudo else ""  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'regularity':
            def key_function(r): return r[1]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'seniority':
            def key_function(r): return r[2]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'non_obsolesence':
            def key_function(r): return r[3]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'continuity':
            def key_function(r): return r[4]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number':
            def key_function(r): return r[5]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

        rank = 1

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            player = num2pseudo[rating[0]] if rating[0] in num2pseudo else ""
            if player == pseudo:
                colour = config.MY_RATING
            else:
                colour = None

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank

                if field == 'player':
                    value = player

                if field == 'regularity':
                    value = rating[1]

                if field == 'seniority':
                    value = rating[2]

                if field == 'non_obsolesence':
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
            rank += 1

        return ratings_table

    def refresh():

        ratings_table = make_ratings_table()

        MY_SUB_PANEL.clear()
        MY_SUB_PANEL <= html.H3("Le classement par régularité")
        MY_SUB_PANEL <= html.DIV("Ce classement une aggrégation par produit de l'ancienneté, la non obsolesence, continuité et le nombre de parties", Class='important')
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


def show_registered_data():
    """ show_registered_data """

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    players_table = html.TABLE()

    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    count = 0
    for data in sorted(players_dict.values(), key=lambda g: g['pseudo'].upper()):
        row = html.TR()
        for field in fields:
            value = data[field]

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les inscrits")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} inscrits")


def show_players_data():
    """ show_players_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    players_alloc = allocations_data['players_dict']

    # gather games to players
    player_games_dict = {}
    for player_id, games_id in players_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    players_table = html.TABLE()

    fields = ['player', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    count = 0
    for player, games in sorted(player_games_dict.items(), key=lambda p: p[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'player':
                value = player
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les joueurs")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} joueurs")
    MY_SUB_PANEL <= html.DIV("Les joueurs dans des parties anonymes ne sont pas pris en compte", Class='note')


def show_game_masters_data():
    """ show_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

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

    masters_alloc = allocations_data['game_masters_dict']

    # gather games to masters
    master_games_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        if master not in master_games_dict:
            master_games_dict[master] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            master_games_dict[master].append(game)

    masters_table = html.TABLE()

    fields = ['master', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'master': 'arbitre', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    masters_table <= thead

    count = 0
    for master, games in sorted(master_games_dict.items(), key=lambda m: m[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'master':
                value = master
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        masters_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les arbitres")
    MY_SUB_PANEL <= masters_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} arbitres")


def show_replacement_data():
    """ show_replacement_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    players_alloc = allocations_data['players_dict']

    # gather games to players
    player_games_dict = {}
    for player_id in players_dict:
        if not players_dict[str(player_id)]['notify_replace']:
            continue
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = []
        if player_id not in players_alloc:
            continue
        games_id = players_alloc[player_id]
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    players_table = html.TABLE()

    fields = ['player', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    count = 0
    for player, games in sorted(player_games_dict.items(), key=lambda p: p[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'player':
                value = player
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les remplaçants")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} abonnés remplaçants")


def show_creators():
    """ show_creators """

    MY_SUB_PANEL <= html.H3("Les créateurs (de partie)")

    priviledged = common.PRIVILEDGED
    if not priviledged:
        return
    creators_list = priviledged['creators']

    creators_table = html.TABLE()

    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    creators_table <= thead

    for creator in sorted(creators_list, key=lambda m: m.upper()):

        row = html.TR()
        col = html.TD(creator)
        row <= col

        creators_table <= row

    MY_SUB_PANEL <= creators_table


def show_moderators():
    """ show_moderators """

    MY_SUB_PANEL <= html.H3("Les modérateurs")

    priviledged = common.PRIVILEDGED
    if not priviledged:
        return
    moderators_list = priviledged['moderators']

    moderators_table = html.TABLE()

    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    moderators_table <= thead

    for moderator in sorted(moderators_list, key=lambda m: m.upper()):

        row = html.TR()
        col = html.TD(moderator)
        row <= col

        moderators_table <= row

    MY_SUB_PANEL <= moderators_table


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

MY_SUB_PANEL = html.DIV(id="ratings")
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
    if item_name == 'Liste inscrits':
        show_registered_data()
    if item_name == 'Liste joueurs':
        show_players_data()
    if item_name == 'Liste arbitres':
        show_game_masters_data()
    if item_name == 'Abonnés remplaçants':
        show_replacement_data()
    if item_name == 'Groupe créateurs':
        show_creators()
    if item_name == 'Groupe modérateurs':
        show_moderators()

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
