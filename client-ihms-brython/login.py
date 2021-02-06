from browser import document, html
from browser.widgets.dialog import InfoDialog

import config

#import requests

#SESSION = requests.Session()

my_panel = html.P()

div = html.DIV(id = "div")
my_panel <= div

form = html.FORM()
div <= form

legend_email = html.LEGEND("email")
form <= legend_email
input_email = html.INPUT(type="email", value="")
form <= input_email
form <= html.BR()

legend_password = html.LEGEND("password")
form <= legend_password
input_password = html.INPUT(type="password", value="")
form <= input_password
form <= html.BR()

def login_callback(ev):
    print(f"login_callback {input_email.value=} {input_password.value=}")

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/login"
    req_result = SESSION.post(url, json={'user_name': pseudo, 'password': password})
    if req_result.status_code != 200:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        tkinter.messagebox.showerror("KO", f"Il y a eu un problème : {message}")
        return

    # very important : extract token for authentication
    json_dict = req_result.json()
    global JWT_TOKEN
    JWT_TOKEN = json_dict['AccessToken']

    print("{JWT_TOKEN=}")



input_login = html.INPUT(type="submit", value="login")
input_login.bind("click",  login_callback)
form <= input_login
form <= html.BR()

def forgot_callback(ev):
    sorry = InfoDialog("Sorry", "Forgot password is not implemented yet")
    form <= sorry

input_forgot = html.INPUT(type="submit", value="forgot password")
input_forgot.bind("click", forgot_callback)
form <= input_forgot
form <= html.BR()

def render(panel_middle):
    panel_middle <= my_panel
