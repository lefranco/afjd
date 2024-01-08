""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

from browser import html, ajax, alert, timer   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import config
import common

import play  # circular import
import play_low


SUPERVISE_REFRESH_TIMER = None


HELP_CONTENT_TABLE = {

    "Comment arrêter la partie ?": "menu “Editer partie“ sous menu “Changer l'état“",
    "Comment changer des joueurs ?": "menu “Editer partie“ sous menu “Déplacer des joueurs“ (en plus de d'attribuer/retirer le rôle)",
    "Comment bénéficier du bouton permettant de contacter tous les remplaçants ?": "retirer le rôle au joueur puis éjecter le joueur de la partie (cf. comment changer des joueurs)",
    "Comment effacer un retard ?": "sous menu “retards“ de la partie et utiliser le bouton “supprimer“ en face du retard",
    "Comment effacer un abandon ?": "sous menu “retards“ de la partie et utiliser le bouton “supprimer“ en face de l'abandon",
    "Comment revenir sur le debriefing ?": "menu “Editer partie“ sous menu “Changer anonymat“ et “Changer accès messagerie“",
}


RANDOM = common.Random()


class Logger(list):
    """ Logger """

    def insert(self, message):
        """ insert """

        # insert datation
        time_stamp_now = time()
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

    def clear_vote_callback(ev, role_id):  # pylint: disable=invalid-name
        """ clear_vote_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'effacement de vote d'arrêt dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'effacement de vote d'arrêt dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le vote a été effacé ! {messages}", True)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        json_dict = {
            'role_id': role_id,
            'value': False
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{play_low.GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        game_master()

    def debrief_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au debrief de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au debrief de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La partie a été modifiée pour le debrief : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/debrief-game/{play_low.GAME}"

        # debrief : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def change_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La date limite a été modifiée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # convert this human entered deadline to the deadline the server understands
        deadline_day_part = input_deadline_day.value
        deadline_hour_part = input_deadline_hour.value

        dt_year, dt_month, dt_day = map(int, deadline_day_part.split('-'))
        dt_hour, dt_min, dt_sec = map(int, deadline_hour_part.split(':'))

        deadline_timestamp = mydatetime.totimestamp(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec)

        time_stamp_now = time()
        if deadline_timestamp < time_stamp_now:
            alert("Désolé, il est interdit de positionner une date limite dans le passé")
            # back to where we were
            play_low.MY_SUB_PANEL.clear()
            game_master()
            return

        json_dict = {
            'name': play_low.GAME,
            'deadline': deadline_timestamp,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def push_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au poussage de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au poussage de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La date limite a été reportée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # get deadline
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

        # add one day - if fast game change to one minute
        time_unit = 60 if play_low.GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_forced = deadline_loaded + time_unit

        # push on server
        json_dict = {
            'name': play_low.GAME,
            'deadline': deadline_forced,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def sync_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la synchro de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la synchro de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La date limite a été synchronisée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # push on server
        json_dict = {
            'name': play_low.GAME,
            'deadline': 0,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_orders_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_recall_orders_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Message de rappel (manque ordres) émis vers : {pseudo_there}")

        ev.preventDefault()

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer les ordres, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Il manque vos ordres et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_agreed_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_recall_agreed_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Message de rappel (manque d'accord pour résoudre) émis vers : {pseudo_there}")

        ev.preventDefault()

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer l'accord, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Il manque votre confirmation d'être d'accord pour résoudre et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_welcome_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_welcome_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de bienvenue : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de bienvenue: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Message de bienvenue émis vers : {pseudo_there}")

        ev.preventDefault()

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Nous avons l'immense honneur de vous informer que vous avez été mis dans la partie et pouvez donc commencer à jouer !"
        body += "\n"
        body += f"Le rôle qui vous a été attribué est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_need_replacement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_need_replacement_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de demande de remplacement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de demande de remplacement: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog("Message de demande de remplacement émis vers les remplaçants potentiels")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Cette partie a besoin d'un remplaçant. Vous aves demandé à être notifié dans un tel cas. Son arbitre vous sollicite !"
        body += "\n"
        body += f"Le rôle qui est libre est {role_name}."
        body += "\n"
        body += "Comment s'y prendre ? Aller sur le site, onglet 'Rejoindre une partie', cliquez sur le bouton dans la colonne 'rejoindre' de la ligne de la partie en rose (Il peut être judicieux d'aller tâter un peu la partie au préalable)"
        body += "\n"
        body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={play_low.GAME}"

        # need to filter here otherwise there would be too many
        players_dict = common.get_players_data()
        if not players_dict:
            alert("Erreur chargement dictionnaire joueurs")
            return
        addressees = [p for p in players_dict if players_dict[str(p)]['notify_replace']]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'replacement',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def civil_disorder_callback(ev, role_id):  # pylint: disable=invalid-name
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le joueur s'est vu imposé un accord pour résoudre: {messages}")

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()

            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = dumps(inforced_names_dict)

        json_dict = {
            'role_id': role_id,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def unallocate_role_callback(ev, pseudo_removed, role_id):  # pylint: disable=invalid-name
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désallocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème Erreur à la désallocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le joueur s'est vu retirer le rôle dans la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def allocate_role_callback(ev, input_for_role, role_id):  # pylint: disable=invalid-name
        """ allocate_role_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def get_list_pseudo_allocatable_game():
        """ get_list_pseudo_allocatable_game """

        pseudo_list = None

        def reply_callback(req):
            nonlocal pseudo_list
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la liste des joueurs allouables dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la liste des joueurs allouables dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return None

            pseudo_list = [play_low.ID2PSEUDO[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{play_low.GAME_ID}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    # check game soloed
    if play_low.GAME_PARAMETERS_LOADED['soloed']:
        alert("La partie est terminée parce qu'un solo a été réalisé !")

    # check game finished (if not soloed)
    elif play_low.GAME_PARAMETERS_LOADED['finished']:
        alert("La partie est arrivée à échéance")

    # warning if game not waiting or ongoing
    if play_low.GAME_PARAMETERS_LOADED['current_state'] not in [0, 1]:
        alert("Attention : la partie est terminée !")

    advancement_loaded = play_low.GAME_PARAMETERS_LOADED['current_advancement']

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        play.load_option(None, 'Consulter')
        return False

    # who can I put in this role
    possible_given_role = get_list_pseudo_allocatable_game()

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

    # incidents
    game_incidents = play_low.game_incidents_reload(play_low.GAME_ID)

    submitted_roles_list = submitted_data['submitted']
    agreed_now_roles_list = submitted_data['agreed_now']
    agreed_after_roles_list = submitted_data['agreed_after']
    needed_roles_list = submitted_data['needed']

    game_admin_table = html.TABLE()

    thead = html.THEAD()
    for field in ['drapeau', 'rôle', 'joueur', '', 'retards', '', 'communiquer la bienvenue', '', 'ordres du joueur', 'demander les ordres', 'mettre en désordre civil', '', 'accord du joueur', 'demander l\'accord', 'forcer l\'accord', '', 'vote du joueur', '', 'retirer le rôle', 'attribuer le rôle']:
        col = html.TD(field)
        thead <= col
    game_admin_table <= thead

    deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
    time_stamp_now = time()

    for role_id in play_low.VARIANT_DATA.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        # flag
        col = html.TD()
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
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
            pseudo_there = play_low.ID2PSEUDO[player_id]
        col <= pseudo_there
        row <= col

        # separator
        col = html.TD()
        row <= col

        # delays
        col = html.TD()
        num_delays = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            num_delays = len([_ for role_id2, _, player_id2, _, _ in game_incidents if role_id2 == role_id and player_id2 is None])
        col <= num_delays
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        input_send_welcome_email = ""
        if str(role_id) not in play_low.VARIANT_CONTENT_LOADED['disorder']:
            if pseudo_there:
                input_send_welcome_email = html.INPUT(type="submit", value="Courriel bienvenue", title="Ceci enverra un courriel de bienvenue au joueur. A utiliser pour un nouveau joueur ou au démarrage de la partie", Class='btn-inside')
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
                    if time_stamp_now > deadline_loaded:
                        input_send_recall_email = html.INPUT(type="submit", value="Courriel rappel ordres", title="Ceci enverra un courriel pour rappeler au joueur d'entrer des ordres dans le système", Class='btn-inside')
                        input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_orders_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_civil_disorder = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                if pseudo_there:
                    if time_stamp_now > deadline_loaded:

                        allowed = play_low.civil_disorder_allowed(advancement_loaded)

                        if allowed:
                            input_civil_disorder = html.INPUT(type="submit", value="Désordre civil", title="Ceci forcera des ordres de désordre civil pour le joueur dans le système", Class='btn-inside')
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
                if role_id in agreed_now_roles_list:
                    flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                elif role_id in agreed_after_roles_list:
                    flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre à la date limite")
                else:
                    flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
        col <= flag
        row <= col

        col = html.TD()
        input_send_recall_email = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_now_roles_list and role_id not in agreed_after_roles_list:
                    if pseudo_there:
                        if time_stamp_now > deadline_loaded:
                            input_send_recall_email = html.INPUT(type="submit", value="Courriel rappel accord", title="Ceci enverra un courriel demandant au joueur de manifester son accord pour résoudre la partie", Class='btn-inside')
                            input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_agreed_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_force_agreement = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_now_roles_list and role_id not in agreed_after_roles_list:
                    if pseudo_there:
                        if time_stamp_now > deadline_loaded:
                            input_force_agreement = html.INPUT(type="submit", value="Forcer accord", title="Ceci forcera l'accord pour résoudre du joueur, déclenchant éventuellement la résolution", Class='btn-inside')
                            input_force_agreement.bind("click", lambda e, r=role_id: force_agreement_callback(e, r))
        col <= input_force_agreement
        row <= col

        # separator
        col = html.TD()
        row <= col
        col = html.TD()

        tab2 = html.TABLE()
        row2 = html.TR()
        if role_id in vote_values_table:

            # must show gm vote value
            col2 = html.TD()
            if vote_values_table[role_id]:
                flag = html.IMG(src="./images/stop.png", title="Le joueur a voté pour arrêter la partie")
            else:
                flag = html.IMG(src="./images/continue.jpg", title="Le joueur a voté pour continuer la partie")
            col2 <= flag
            row2 <= col2

            # gm must be able to clear vote
            col2 = html.TD()
            form = html.FORM()
            clear_vote = html.INPUT(type="submit", value="X", Class='btn-inside')
            clear_vote.bind("click", lambda ev, r=role_id: clear_vote_callback(ev, r))
            form <= clear_vote
            col2 <= form
            row2 <= col2

        tab2 <= row2
        col <= tab2
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        input_unallocate_role = ""
        if str(role_id) not in play_low.VARIANT_CONTENT_LOADED['disorder']:
            if pseudo_there:
                input_unallocate_role = html.INPUT(type="submit", value="Retirer le rôle", title="Ceci enlèvera le rôle au joueur", Class='btn-inside')
                input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
        col <= input_unallocate_role
        row <= col

        col = html.TD()
        form = ""
        if not pseudo_there:

            if not possible_given_role:

                form = html.FORM()
                input_contact_replacers = html.INPUT(type="submit", value="Contacter les remplaçants", title="Ceci contactera tous les remplaçants déclarés volontaires du site", display='inline', Class='btn-inside')
                input_contact_replacers.bind("click", lambda e, r=role_id: send_need_replacement_callback(e, r))
                form <= input_contact_replacers

            elif not (play_low.GAME_PARAMETERS_LOADED['current_state'] == 0 and not play_low.GAME_PARAMETERS_LOADED['manual']):

                form = html.FORM()
                input_for_role = html.SELECT(type="select-one", value="", display='inline', Class='btn-inside')
                for play_role_pseudo in sorted(possible_given_role, key=lambda p: p.upper()):
                    option = html.OPTION(play_role_pseudo)
                    input_for_role <= option
                form <= input_for_role
                form <= " "
                input_put_in_role = html.INPUT(type="submit", value="Attribuer le rôle", title="Ceci attribuera le rôle au joueur", display='inline', Class='btn-inside')
                input_put_in_role.bind("click", lambda e, i=input_for_role, r=role_id: allocate_role_callback(e, i, r))
                form <= input_put_in_role

        col <= form
        row <= col

        game_admin_table <= row

    deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

    # form for debrief

    deadline_form = html.FORM()

    dl_gmt = html.DIV("ATTENTION : vous devez entrer une date limite en temps GMT", Class='important')
    special_legend = html.LEGEND(dl_gmt)
    deadline_form <= special_legend
    deadline_form <= html.BR()

    # get GMT date and time
    time_stamp_now = time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

    # convert 'deadline_loaded' to human editable format

    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
    datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
    deadline_loaded_day, deadline_loaded_hour, _ = datetime_deadline_loaded_str.split(' ')

    fieldset = html.FIELDSET()
    legend_deadline_day = html.LEGEND("Jour de la date limite (DD/MM/YYYY - ou selon les réglages du navigateur)", title="La date limite. Dernier jour pour soumettre les ordres. Après le joueur est en retard.")
    fieldset <= legend_deadline_day
    input_deadline_day = html.INPUT(type="date", value=deadline_loaded_day, Class='btn-inside')
    fieldset <= input_deadline_day
    deadline_form <= fieldset

    fieldset = html.FIELDSET()
    legend_deadline_hour = html.LEGEND("Heure de la date limite (hh:mm ou selon les réglages du navigateur)", title="La date limite. Dernière heure du jour pour soumettre les ordres. Après le joueur est en retard.")
    fieldset <= legend_deadline_hour
    input_deadline_hour = html.INPUT(type="time", value=deadline_loaded_hour, step=1, Class='btn-inside')
    fieldset <= input_deadline_hour
    deadline_form <= fieldset

    input_change_deadline_game = html.INPUT(type="submit", value="Changer la date limite de la partie à cette valeur", Class='btn-inside')
    input_change_deadline_game.bind("click", change_deadline_game_callback)
    deadline_form <= input_change_deadline_game

    deadline_form <= html.BR()
    deadline_form <= html.BR()
    deadline_form <= html.BR()

    input_push_deadline_game = html.INPUT(type="submit", value="Reporter la date limite de 24 heures (une minute pour une partie en direct)", Class='btn-inside')
    input_push_deadline_game.bind("click", push_deadline_game_callback)
    deadline_form <= input_push_deadline_game

    deadline_form <= html.BR()
    deadline_form <= html.BR()
    deadline_form <= html.BR()

    input_push_deadline_game = html.INPUT(type="submit", value="Mettre la date limite à maintenant", Class='btn-inside')
    input_push_deadline_game.bind("click", sync_deadline_game_callback)
    deadline_form <= input_push_deadline_game

    # form for debrief

    debrief_form = html.FORM()

    debrief_action = html.DIV("Lève l'anonymat et ouvre les canaux de communication (réversible)", Class='None')
    special_legend = html.LEGEND(debrief_action)
    debrief_form <= special_legend

    debrief_form <= html.BR()
    input_debrief_game = html.INPUT(type="submit", value="Debrief !", Class='btn-inside')
    input_debrief_game.bind("click", debrief_game_callback)
    debrief_form <= input_debrief_game

    play_low.MY_SUB_PANEL <= html.H3("Gestion")

    play_low.MY_SUB_PANEL <= game_admin_table

    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [0, 1]:

        play_low.MY_SUB_PANEL <= html.H3("Date limite")

        play_low.MY_SUB_PANEL <= deadline_form
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")

        play_low.MY_SUB_PANEL <= html.H3("Debrief de la partie")

        if not (play_low.GAME_PARAMETERS_LOADED['finished'] or play_low.GAME_PARAMETERS_LOADED['soloed']):
            play_low.MY_SUB_PANEL <= "Partie toujours en cours..."
        else:
            play_low.MY_SUB_PANEL <= debrief_form

    play_low.MY_SUB_PANEL <= html.H3("Aide mémoire")

    help_table = html.TABLE()
    for question_txt, answer_txt in HELP_CONTENT_TABLE.items():

        row = html.TR()

        col = html.TD()
        col <= html.B(question_txt)
        row <= col

        col = html.TD()
        col <= answer_txt
        row <= col

        help_table <= row

    play_low.MY_SUB_PANEL <= help_table

    return True


def supervise():
    """ supervise """

    role2pseudo = {}
    log_stack = None

    def civil_disorder_callback(ev, role_id):  # pylint: disable=invalid-name
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        if ev is not None:
            ev.preventDefault()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = loads(req.text)
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
                common.info_dialog("La résolution a été forcée..")
                message = "Résolution forcée par la console suite forçage accord"
                log_stack.insert(message)

        if ev is not None:
            ev.preventDefault()

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = dumps(inforced_names_dict)

        json_dict = {
            'role_id': role_id,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reload_game_admin_table(submitted_data, votes):
        """ reload_game_admin_table """

        vote_values_table = {}
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_now_roles_list = submitted_data['agreed_now']
        agreed_after_roles_list = submitted_data['agreed_after']
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
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
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
                pseudo_there = play_low.ID2PSEUDO[player_id]
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
                    if role_id in agreed_now_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                    elif role_id in agreed_after_roles_list:
                        flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre à la date limite")
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
        time_stamp_now = time()

        # are we past ?
        if time_stamp_now > force_point:

            submitted_roles_list = submitted_data['submitted']
            agreed_now_roles_list = submitted_data['agreed_now']
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
                    if role_id in submitted_roles_list and role_id not in agreed_now_roles_list:
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

        dialog.close(None)

        play.load_option(None, 'Consulter')

    def supervise_callback(_, dialog):
        """ supervise_callback """

        dialog.close(None)

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
    dialog = mydialog.Dialog("On supervise vraiment la partie (cela peut entrainer des désordres civils) ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: supervise_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_supervise_callback(e, d))

    return True
