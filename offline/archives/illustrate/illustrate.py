

import base64

# display
if image_str:

    # get back image as it was - b64 decode to get it from server
    image_bytes = base64.standard_b64decode(image_str.encode())

    # make it a displayable picture
    image_b64 = base64.b64encode(image_bytes).decode()

    # put it on screen
    MY_SUB_PANEL <= html.IMG(src=f"data:image/jpeg;base64,{image_b64}", alt=name)




def illustrate_event():
    """ illustrate_event """

    def put_picture_event_callback(_):
        """ put_picture_event_callback """

        def onload_callback(_):
            """ onload_callback """

            def reply_callback(req):
                req_result = json.loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à l'illustration de l'événement : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à l'illustration de l'événement : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                InfoDialog("OK", f"L'événement a été illustré : {messages}", remove_after=config.REMOVE_AFTER)

            # get the image content
            image_bytes = bytes(window.Array["from"](window.Uint8Array.new(reader.result)))

            if len(image_bytes) > MAX_IMAGE_SIZE:
                alert(f"Ce fichier est trop gros La limite est {MAX_IMAGE_SIZE} octets")
                return

            # b64 encode to pass it on server
            try:
                image_str = base64.standard_b64encode(image_bytes).decode()
            except:  # noqa: E722 pylint: disable=bare-except
                alert("Problème à l'encodage pour le web... ")
                return

            json_dict = {
                'image': image_str
            }

            host = config.SERVER_CONFIG['PLAYER']['HOST']
            port = config.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/events/{event_id}"

            # illustrating an event : need token
            ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        if not INPUT_FILE.files:

            alert("Pas de fichier")

            # back to where we started
            MY_SUB_PANEL.clear()
            illustrate_event()
            return

        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Extract the file
        file_name = INPUT_FILE.files[0]
        # Read the file content as text
        reader.bind("load", onload_callback)
        reader.readAsArrayBuffer(file_name)

        # back to where we started
        MY_SUB_PANEL.clear()
        illustrate_event()

    def remove_picture_event_callback(_):
        """ remove_picture_event_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la non illustration de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la non illustration de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'événement a été non illustré : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {
            'image': ''
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events/{event_id}"

        # illustrating an event : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        illustrate_event()

    MY_SUB_PANEL <= html.H3("Illustration d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return
    pseudo = storage['PSEUDO']

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_name = storage['EVENT']
    events_dict = common.get_events_data()
    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("Ficher JPG uniquement !")
    fieldset <= legend_name
    form <= fieldset

    # need to make this global to keep it (only way it seems)
    global INPUT_FILE
    if INPUT_FILE is None:
        INPUT_FILE = html.INPUT(type="file", accept='.jpg')
    form <= INPUT_FILE
    form <= html.BR()

    form <= html.BR()

    input_put_picture = html.INPUT(type="submit", value="mettre cette image")
    input_put_picture.bind("click", put_picture_event_callback)
    form <= input_put_picture

    input_remove_picture = html.INPUT(type="submit", value="retirer l'image")
    input_remove_picture.bind("click", remove_picture_event_callback)
    form <= input_remove_picture

    MY_SUB_PANEL <= html.DIV(f"Evénement {event_name}", Class='important')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form

