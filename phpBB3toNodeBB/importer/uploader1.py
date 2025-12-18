#!/usr/bin/env python3
 
import re
import requests

s = requests.Session()


# 1. get login page (HTML)
r = s.get("https://forum.diplomania2.fr/login")
html = r.text

m = re.search(r'name="_csrf" value="([^"]+)"', html)
assert m, "CSRF not found in login page"
csrf = m.group(1)

print("csrf:", csrf)

# 2. login
login = s.post(
    "https://forum.diplomania2.fr/login",
    data={
        "username": "admin",
        "password": "admin123",
        "_csrf": csrf,
    }
)

print("cookies:", s.cookies.get_dict())

# 3. upload
with open("toto", "rb") as f:
    r = s.post(
        "https://forum.diplomania2.fr/api/v3/files",
        files={"files[]": f}
    )

print(r.status_code)
print(r.text)
