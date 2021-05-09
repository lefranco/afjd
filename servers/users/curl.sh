

# Add an account (do not need token)
#curl -H "Content-Type: application/json" -X POST -d '{"user_name":"John","password":"Doe"}' https://afjd1.eu.ngrok.io:443/add


# Register a login (exports a token) - fails bad password
#curl -H "Content-Type: application/json" -X POST   -d '{"user_name":"John","password":"Doe?"}' https://afjd1.eu.ngrok.io:443/login


# Register a login (exports a token)  - success good password
#curl -H "Content-Type: application/json" -X POST   -d '{"user_name":"John","password":"Doe"}' https://afjd1.eu.ngrok.io:443/login

# you must do export ACCESS= < result previous comand > to be granted access

# Change password account (need token)
#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" -X POST -d '{"user_name":"John","password":"Didi"}' https://afjd1.eu.ngrok.io:443/change

# you must do export ACCESS= < result previous comand > to be granted access

# Checks token (should succeed)
#curl -H "Authorization: Bearer $ACCESS" https://afjd1.eu.ngrok.io:443/verify

# Deletes account (need token)
#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" -X POST -d '{"user_name":"John"}' https://afjd1.eu.ngrok.io:443/remove


