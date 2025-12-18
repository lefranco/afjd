#!/usr/bin/env python3
import re
import requests

s = requests.Session()

# 1. Get login page and CSRF token
r = s.get("https://forum.diplomania2.fr/login")
html = r.text
print(html)
m = re.search(r'name="_csrf" value="([^"]+)"', html)
csrf = m.group(1)
print("Login CSRF:", csrf)

# 2. Login
s.post(
    "https://forum.diplomania2.fr/login",
    data={"username": "admin", "password": "admin123", "_csrf": csrf}
)
print("Cookies:", s.cookies.get_dict())

# Get the CSRF token for API calls (from JS)
r = s.get("https://forum.diplomania2.fr/api/config")
config = r.json()
api_csrf = config.get('csrfToken')
print("API CSRF Token:", api_csrf)

# 3. Test Upload with CSRF Token Header
endpoints_to_test = [
    "/api/post/upload",           # Most commonly referenced[citation:7][citation:10]
    "/api/admin/upload/file",     # Admin-specific endpoint[citation:6][citation:7]
]

headers = {
    "X-CSRF-Token": api_csrf      # This header is crucial for POST requests[citation:9]
}

for endpoint in endpoints_to_test:
    print(f"\n--- Testing {endpoint} ---")
    with open("toto", "rb") as f:
        # Important: Use 'files' for multipart/form-data and 'data' for other params
        r = s.post(
            f"https://forum.diplomania2.fr{endpoint}",
            files={"files[]": f},
            data={"_uid": "1"},  # Specify the user ID
            headers=headers
        )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")