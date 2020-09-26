

# create a player C
# curl http://localhost:5002/players -d 'pseudo=Tartempion&email=toto@labas.com&telephone=111&first_name=Anne&family_name=Hidalgo&country=Angleterre&time_zone=UTC + 1' -X POST

# get data of a player R
#curl http://localhost:5002/players/Zorglub

# update data a player U
curl http://localhost:5002/players -d 'pseudo=Zorglub&email=titi@labas.com' -X PUT

# delete player D
##curl http://localhost:5002/players/s -X DELETE

# get all players
curl http://localhost:5002/players  -X GET
