#!/usr/bin/env python3

"""
At last a file importer that works
"""

import requests
import urllib3

### pip3 install pip-system-certs --break-system-packages  # at company only ?

# Suppress the warning messages in the console
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # at company only ?


def main():

    session = requests.Session()
    #session.verify = False   # at company only

    # Very important
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    base_url = "https://forum.diplomania2.fr"

    # ------------------
    # 1. Get the initial CSRF from the config API (even before login)
    # ------------------

    print("--- Fetching Initial CSRF ---")
    r_config = session.get(f"{base_url}/api/config")
    init_data = r_config.json()
    csrf = init_data.get('csrf_token')

    print(f"Initial CSRF: {csrf}")

    if not csrf:
        print("Failed to get initial CSRF token.")
        return

    # ------------------
    # 2. Login using csrf
    # ------------------

    print("\n--- Logging In ---")
    login_payload = {
        "username": "admin",
        "password": "admin123",
        "_csrf": csrf
    }
    r_login = session.post(f"{base_url}/login", data=login_payload)

    print(f"Login Status: {r_login.status_code}")
    print(f"Login Response: {r_login.text}")

    if r_login.status_code != 200:
        print("Failed to log in.")
        return

    # ------------------
    # 3. Verify Login and Get Authenticated Token
    # ------------------

    print("\n--- Checking login ok ---")
    r_api_config = session.get(f"{base_url}/api/config")
    config_data = r_api_config.json()

    is_logged_in = config_data.get('loggedIn', False)
    api_csrf = config_data.get('csrf_token')

    print(f"Logged In Status: {is_logged_in}")
    print(f"Authenticated API CSRF: {api_csrf}")

    if not is_logged_in:
        print("!! LOGIN FAILED !! Check credentials or CSRF handling.")
        return

    # ------------------
    # 4. Upload the file
    # ------------------

    print("\n--- Uploading the file ---")

    file = "./sample.jpeg"
    url = f"{base_url}/api/post/upload"
    data = {"_csrf": api_csrf}
    try:
        with open(file, "rb") as file_ptr:
            files = {"files[]": (file, file_ptr, "text/plain")}
            r_upload = session.post(url, files=files, data=data)

        print(f"URL: {url}")
        print(f"data: {data}")
        print(f"Upload Status: {r_upload.status_code}")
        print(f"Upload Response: {r_upload.text}")
    except FileNotFoundError:
        print(f"File '{file}' not found.")
        return

    if r_upload.status_code not in [200, 201]:
        print("Upload failed")
        return

    print(f"Upload of {file} successful !!!")


if __name__ == "__main__":
    main()
