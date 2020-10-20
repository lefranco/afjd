

# Add an account (do not need token)
#curl -H "Content-Type: application/json" -X POST -d '{"user_name":"John","password":"Doe"}' http://localhost:5001/add_user


# Register a login (exports a token) - fails bad password
#curl -H "Content-Type: application/json" -X POST   -d '{"user_name":"John","password":"Doe?"}' http://localhost:5001/login_user


# Register a login (exports a token)  - success good password
#curl -H "Content-Type: application/json" -X POST   -d '{"user_name":"John","password":"Doe"}' http://localhost:5001/login_user

# you must do export ACCESS= < result previous comand > to be granted access

# Change password account (need token)
#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" -X POST -d '{"user_name":"John","password":"Didi"}' http://localhost:5001/change_user

# list of accounts (this should not stay in production)
#curl http://localhost:5001/debug

# you must do export ACCESS= < result previous comand > to be grated access

# Checks token (should succeed)
#curl -H "Authorization: Bearer $ACCESS" http://localhost:5001/verify_user

# Deletes account (need token)
#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" -X POST -d '{"user_name":"John"}' http://localhost:5001/remove_user


# list of accounts (this should not stay in production)
#curl http://localhost:5001/debug
