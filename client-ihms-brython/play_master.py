""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import time
import json

from browser import html, ajax, alert, timer   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common

import play  # circular import
import play_low


SUPERVISE_REFRESH_TIMER = None


class Random:
    """ Random provider """

    def __init__(self):
        self._seed = int(time.time())

    def choice(self, values):
        """ chooses an element """

        self._seed += 1
        a_val = self._seed * 15485863
        position = int(a_val ** 3 % 2038074743 / 2038074743)
        return values[position]


RANDOM = Random()


class Logger(list):
    """ Logger """

    def insert(self, message):
        """ insert """

        # insert datation
        time_stamp_now = time.time()
        date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

        # put in stack (limited height)
        log_line = html.DIV(f"{date_now_gmt_str} : {message}", Class='important')
        self.append(log_line)

    def display(self, log_window):
        """ display """

        for log_line in reversed(self):
            log_window <= log_line


def stack_clock(frame, period):
    """ stack_clock """

    clock_icon_img = html.IMG(src="./images/clock.png", title=f"Cette page est rafraichie périodiquement toutes les {period} secondes")
    frame <= clock_icon_img


# how long between two consecutives refresh
SUPERVISE_REFRESH_PERIOD_SEC = 15


def game_master():
    """ game_master """

    def change_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la date limite à la partie : {req_result['msg']}")

                    # back to where we were
                    play_low.MY_SUB_PANEL.clear()
                    game_master()
                    return

                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été modifiée : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        # convert this human entered deadline to the deadline the server understands
        deadline_day_part = input_deadline_day.value
        deadline_hour_part = input_deadline_hour.value

        dt_year, dt_month, dt_day = map(int, deadline_day_part.split('-'))
        dt_hour, dt_min, dt_sec = map(int, deadline_hour_part.split(':'))

        deadline_timestamp = mydatetime.totimestamp(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec)

        time_stamp_now = time.time()
        if deadline_timestamp < time_stamp_now:
            alert("Désolé, il est interdit de positionner une date limite dans le passé")
            # back to where we were
            play_low.MY_SUB_PANEL.clear()
            game_master()
            return

        json_dict = {
            'pseudo': play_low.PSEUDO,
            'name': play_low.GAME,
            'deadline': deadline_timestamp,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def push_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au poussage de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au poussage de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été reportée : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        # get deadline
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

        # add one day - if fast game change to one minute
        time_unit = 60 if play_low.GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_forced = deadline_loaded + time_unit

        # push on server
        json_dict = {
            'pseudo': play_low.PSEUDO,
            'name': play_low.GAME,
            'deadline': deadline_forced,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def sync_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la synchro de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la synchro de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été reportée : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        # push on server
        json_dict = {
            'pseudo': play_low.PSEUDO,
            'name': play_low.GAME,
            'deadline': 0,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_orders_email_callback(_, role_id):
        """ send_recall_orders_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de rappel (manque ordres) émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time.time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer les ordres, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Il manque vos ordres et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': play_low.PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_agreed_email_callback(_, role_id):
        """ send_recall_agreed_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de rappel (manque d'accord pour résoudre) émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time.time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer l'accord, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Il manque votre confirmation d'être d'accord pour résoudre et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': play_low.PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_welcome_email_callback(_, role_id):
        """ send_welcome_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de bienvenue : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de bienvenue: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de bienvenue émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "J'ai l'immense honneur de vous informer que vous avez été mis dans la partie et pouvez donc commencer à jouer !"
        body += "\n"
        body += f"Le rôle qui vous a été attribué est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': play_low.PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_need_replacement_callback(_, role_id):
        """ send_need_replacement_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de demande de remplacement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de demande de remplacement: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", "Message de demande de remplacement émis vers les remplaçants potentiels", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Cette partie a besoin d'un remplaçant. Vous aves demandé à être notifié dans un tel cas. Son arbitre vous sollicite !"
        body += "\n"
        body += f"Le rôle qui est libre est {role_name}."
        body += "\n"
        body += "Comment s'y prendre ? Aller sur le site, onglet 'Rejoindre une partie', bouton 'j'en profite' de la ligne de la partie en rose (Il peut être judicieux d'aller tâter un peu la partie au préalable)"
        body += "\n"
        body += "Si ces notifications vous agacent, allez sur le site modifier votre compte..."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        players_dict = common.get_players_data()
        if not players_dict:
            alert("Erreur chargement dictionnaire joueurs")
            return
        addressees = [p for p in players_dict if players_dict[str(p)]['replace']]

        json_dict = {
            'pseudo': play_low.PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': play_low.PSEUDO,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu imposé un accord pour résoudre: {messages}", remove_after=config.REMOVE_AFTER)

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            play_low.load_special_stuff()
            game_master()

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = json.dumps(inforced_names_dict)

        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': play_low.PSEUDO,
            'definitive': definitive_value,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def unallocate_role_callback(_, pseudo_removed, role_id):
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désallocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème Erreur à la désallocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu retirer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1,
            'pseudo': play_low.PSEUDO,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def allocate_role_callback(_, input_for_role, role_id):
        """ allocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0,
            'pseudo': play_low.PSEUDO,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def get_list_pseudo_allocatable_game(id2pseudo):
        """ get_list_pseudo_allocatable_game """

        pseudo_list = None

        def reply_callback(req):
            nonlocal pseudo_list
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la liste des joueurs allouables dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la liste des joueurs allouables dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return None

            pseudo_list = [id2pseudo[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{play_low.GAME_ID}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return pseudo_list

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to be game master
    if play_low.ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        play.load_option(None, 'Consulter')
        return False

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}
    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        play.load_option(None, 'Consulter')
        return False

    # who can I put in this role
    possible_given_role = get_list_pseudo_allocatable_game(id2pseudo)

    # votes

    votes = play_low.game_votes_reload(play_low.GAME_ID)
    if votes is None:
        alert("Erreur chargement votes")
        play.load_option(None, 'Consulter')
        return False

    votes = list(votes)

    vote_values_table = {}
    for _, role, vote_val in votes:
        vote_values_table[role] = bool(vote_val)

    submitted_roles_list = submitted_data['submitted']
    agreed_roles_list = submitted_data['agreed']
    needed_roles_list = submitted_data['needed']

    game_admin_table = html.TABLE()

    thead = html.THEAD()
    for field in ['drapeau', 'rôle', 'joueur', 'communiquer la bienvenue', '', 'ordres du joueur', 'demander les ordres', 'mettre en désordre civil', '', 'accord du joueur', 'demander l\'accord', 'forcer l\'accord', '', 'vote du joueur', '', 'retirer le rôle', 'attribuer le rôle']:
        col = html.TD(field)
        thead <= col
    game_admin_table <= thead

    for role_id in play_low.VARIANT_DATA.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        # flag
        col = html.TD()
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)
        col <= role_icon_img
        row <= col

        # role name
        col = html.TD()
        col <= role_name
        row <= col

        # player
        col = html.TD()
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col <= pseudo_there
        row <= col

        col = html.TD()
        input_send_welcome_email = ""
        if pseudo_there:
            input_send_welcome_email = html.INPUT(type="submit", value="courriel bienvenue", title="Ceci enverra un courriel de bienvenue au joueur. A utiliser pour un nouveau joueur ou au démarrage de la partie")
            input_send_welcome_email.bind("click", lambda e, r=role_id: send_welcome_email_callback(e, r))
        col <= input_send_welcome_email
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
            else:
                flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
        col <= flag
        row <= col

        col = html.TD()
        input_send_recall_email = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                if pseudo_there:
                    input_send_recall_email = html.INPUT(type="submit", value="courriel rappel ordres", title="Ceci enverra un courriel pour rappeler au joueur d'entrer des ordres dans le système")
                    input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_orders_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_civil_disorder = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                if pseudo_there:
                    input_civil_disorder = html.INPUT(type="submit", value="désordre civil", title="Ceci forcera des ordres de désordre civil pour le joueur dans le système")
                    input_civil_disorder.bind("click", lambda e, r=role_id: civil_disorder_callback(e, r))
        col <= input_civil_disorder
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id in agreed_roles_list:
                    flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                else:
                    flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
        col <= flag
        row <= col

        col = html.TD()
        input_send_recall_email = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_roles_list:
                    input_send_recall_email = html.INPUT(type="submit", value="courriel rappel accord", title="Ceci enverra un courriel demandant au joueur de manifester son accord pour résoudre la partie")
                    input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_agreed_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_force_agreement = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_roles_list:
                    input_force_agreement = html.INPUT(type="submit", value="forcer accord", title="Ceci forcera l'accord pour résoudre du joueur, déclenchant éventuellement la résolution")
                    input_force_agreement.bind("click", lambda e, r=role_id: force_agreement_callback(e, r))
        col <= input_force_agreement
        row <= col

        # separator
        col = html.TD()
        row <= col
        col = html.TD()

        flag = ""
        if role_id in vote_values_table:
            if vote_values_table[role_id]:
                flag = html.IMG(src="./images/stop.png", title="Le joueur a voté pour arrêter la partie")
            else:
                flag = html.IMG(src="./images/continue.jpg", title="Le joueur a voté pour continuer la partie")
        col <= flag
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        input_unallocate_role = ""
        if pseudo_there:
            input_unallocate_role = html.INPUT(type="submit", value="retirer le rôle", title="Ceci enlèvera le rôle au joueur")
            input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
        col <= input_unallocate_role
        row <= col

        col = html.TD()
        form = ""
        if not pseudo_there:
            form = html.FORM()

            if not possible_given_role:

                input_contact_replacers = html.INPUT(type="submit", value="contacter les remplaçants", title="Ceci contactera tous les remplaçants déclarés volontaires du site", display='inline')
                input_contact_replacers.bind("click", lambda e, r=role_id: send_need_replacement_callback(e, r))
                form <= input_contact_replacers

            else:

                input_for_role = html.SELECT(type="select-one", value="", display='inline')
                for play_role_pseudo in sorted(possible_given_role, key=lambda p: p.upper()):
                    option = html.OPTION(play_role_pseudo)
                    input_for_role <= option
                form <= input_for_role
                form <= " "
                input_put_in_role = html.INPUT(type="submit", value="attribuer le rôle", title="Ceci attribuera le rôle au joueur", display='inline')
                input_put_in_role.bind("click", lambda e, i=input_for_role, r=role_id: allocate_role_callback(e, i, r))
                form <= input_put_in_role

        col <= form
        row <= col

        game_admin_table <= row

    deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

    deadline_form = html.FORM()

    dl_gmt = html.DIV("ATTENTION : vous devez entrer une date limite en temps GMT", Class='important')
    special_legend = html.LEGEND(dl_gmt)
    deadline_form <= special_legend
    deadline_form <= html.BR()

    # get GMT date and time
    time_stamp_now = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

    # convert 'deadline_loaded' to human editable format

    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
    datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
    deadline_loaded_day, deadline_loaded_hour, _ = datetime_deadline_loaded_str.split(' ')

    fieldset = html.FIELDSET()
    legend_deadline_day = html.LEGEND("Jour de la date limite (DD/MM/YYYY - ou selon les réglages du navigateur)", title="La date limite. Dernier jour pour soumettre les ordres. Après le joueur est en retard.")
    fieldset <= legend_deadline_day
    input_deadline_day = html.INPUT(type="date", value=deadline_loaded_day)
    fieldset <= input_deadline_day
    deadline_form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("Heure de la date limite (hh:mm ou selon les réglages du navigateur)", title="La date limite. Dernière heure du jour pour soumettre les ordres. Après le joueur est en retard.")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="time", value=deadline_loaded_hour)
    fieldset <= input_deadline_hour
    deadline_form <= fieldset

    input_change_deadline_game = html.INPUT(type="submit", value="changer la date limite de la partie à cette valeur")
    input_change_deadline_game.bind("click", change_deadline_game_callback)
    deadline_form <= input_change_deadline_game

    deadline_form <= html.BR()
    deadline_form <= html.BR()
    deadline_form <= html.BR()

    input_push_deadline_game = html.INPUT(type="submit", value="reporter la date limite de 24 heures (une minute pour une partie en direct)")
    input_push_deadline_game.bind("click", push_deadline_game_callback)
    deadline_form <= input_push_deadline_game

    deadline_form <= html.BR()
    deadline_form <= html.BR()
    deadline_form <= html.BR()

    input_push_deadline_game = html.INPUT(type="submit", value="mettre la date limite à maintenant")
    input_push_deadline_game.bind("click", sync_deadline_game_callback)
    deadline_form <= input_push_deadline_game

    play_low.MY_SUB_PANEL <= html.H3("Gestion")

    play_low.MY_SUB_PANEL <= game_admin_table
    play_low.MY_SUB_PANEL <= html.BR()

    play_low.MY_SUB_PANEL <= html.DIV("Pour bénéficier du bouton premettant de contacter tous les remplaçants, il faut retirer le rôle au joueur (ci-dessous) puis éjecter le joueur de la partie (dans le menu appariement.)", Class='note')

    play_low.MY_SUB_PANEL <= html.H3("Date limite")

    play_low.MY_SUB_PANEL <= deadline_form
    play_low.MY_SUB_PANEL <= html.BR()

    play_low.MY_SUB_PANEL <= html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    play_low.MY_SUB_PANEL <= html.BR()

    return True


def supervise():
    """ supervise """

    id2pseudo = {}
    role2pseudo = {}
    log_stack = None

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': play_low.PSEUDO,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            adjudicated = req_result['adjudicated']
            if adjudicated:
                InfoDialog("OK", "La résolution a été forcée..", remove_after=config.REMOVE_AFTER)
                message = "Résolution forcée par la console suite forçage accord"
                log_stack.insert(message)

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = json.dumps(inforced_names_dict)

        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': play_low.PSEUDO,
            'definitive': definitive_value,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reload_game_admin_table(submitted_data, votes):
        """ reload_game_admin_table """

        vote_values_table = {}
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_roles_list = submitted_data['agreed']
        needed_roles_list = submitted_data['needed']

        game_admin_table = html.TABLE()

        for role_id in play_low.VARIANT_DATA.roles:

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

            # flag
            col = html.TD()
            role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # player
            col = html.TD()
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]
            col <= pseudo_there
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in vote_values_table:
                if vote_values_table[role_id]:
                    flag = html.IMG(src="./images/stop.png", title="Arrêter la partie")
                else:
                    flag = html.IMG(src="./images/continue.jpg", title="Continuer la partie")
            col <= flag
            row <= col

            game_admin_table <= row

        return game_admin_table

    def refresh():
        """ refresh """

        submitted_data = {}
        votes = None

        def refresh_subroutine():

            # reload from server to see what changed from outside
            play_low.load_dynamic_stuff()
            nonlocal submitted_data
            submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
            if not submitted_data:
                alert("Erreur chargement données de soumission")
                return

            # votes
            nonlocal votes
            votes = play_low.game_votes_reload(play_low.GAME_ID)
            if votes is None:
                alert("Erreur chargement votes")
                return
            votes = list(votes)

            play_low.MY_SUB_PANEL.clear()

            # clock
            stack_clock(play_low.MY_SUB_PANEL, SUPERVISE_REFRESH_PERIOD_SEC)
            play_low.MY_SUB_PANEL <= html.BR()

            # game status
            play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
            play_low.MY_SUB_PANEL <= html.BR()

            # role flag
            play_low.stack_role_flag(play_low.MY_SUB_PANEL)

        # changed from outside
        refresh_subroutine()

        # calculate deadline + grace
        time_unit = 60 if play_low.GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        grace_duration_loaded = play_low.GAME_PARAMETERS_LOADED['grace_duration']
        force_point = deadline_loaded + time_unit * grace_duration_loaded
        time_stamp_now = time.time()

        # are we past ?
        if time_stamp_now > force_point:

            submitted_roles_list = submitted_data['submitted']
            agreed_roles_list = submitted_data['agreed']
            needed_roles_list = submitted_data['needed']

            missing_orders = []
            for role_id in play_low.VARIANT_DATA.roles:
                if role_id in needed_roles_list and role_id not in submitted_roles_list:
                    missing_orders.append(role_id)

            alterated = False
            if missing_orders:
                role_id = RANDOM.choice(missing_orders)
                civil_disorder_callback(None, role_id)
                role = play_low.VARIANT_DATA.roles[role_id]
                role_name = play_low.VARIANT_DATA.role_name_table[role]
                message = f"Désordre civil pour {role_name}"
                alterated = True
            else:
                missing_agreements = []
                for role_id in play_low.VARIANT_DATA.roles:
                    if role_id in submitted_roles_list and role_id not in agreed_roles_list:
                        missing_agreements.append(role_id)
                if missing_agreements:
                    role_id = RANDOM.choice(missing_agreements)
                    force_agreement_callback(None, role_id)
                    role = play_low.VARIANT_DATA.roles[role_id]
                    role_name = play_low.VARIANT_DATA.role_name_table[role]
                    message = f"Forçage accord pour {role_name}"
                    alterated = True

            if alterated:

                log_stack.insert(message)

                # changed from myself
                refresh_subroutine()

        game_admin_table = reload_game_admin_table(submitted_data, votes)
        play_low.MY_SUB_PANEL <= game_admin_table
        play_low.MY_SUB_PANEL <= html.BR()

        # put stack in log window
        log_window = html.DIV(id="log")
        log_stack.display(log_window)

        # display
        play_low.MY_SUB_PANEL <= log_window

    def cancel_supervise_callback(_, dialog):
        """ cancel_supervise_callback """

        dialog.close()

        play.load_option(None, 'Consulter')

    def supervise_callback(_, dialog):
        """ supervise_callback """

        dialog.close()

        nonlocal id2pseudo
        id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

        nonlocal role2pseudo
        role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

        nonlocal log_stack
        log_stack = Logger()

        # initiates refresh
        refresh()

        # repeat
        global SUPERVISE_REFRESH_TIMER
        if SUPERVISE_REFRESH_TIMER is None:
            SUPERVISE_REFRESH_TIMER = timer.set_interval(refresh, SUPERVISE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to be game master
    if play_low.ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be fast
    if not play_low.GAME_PARAMETERS_LOADED['fast']:
        alert("Cette partie n'est pas une partie rapide")
        play.load_option(None, 'Consulter')
        return False

    # since touchy, this requires a confirmation
    dialog = Dialog("On supervise vraiment la partie (cela peut entrainer des désordres civils) ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: supervise_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_supervise_callback(e, d))

    return True