

# create a player C
curl http://localhost:5003/players -d 'pseudo=Tartempion&password=Tartempion&email=toto@labas.com&telephone=111&first_name=John&family_name=Doe&country=FRA&time_zone=UTC + 1' -X POST

# get data of a player R
#curl http://localhost:5003/players/Zorglub

# update data a player U
# curl http://localhost:5003/players -d 'pseudo=Zorglub&email=titi@labas.com' -X PUT


# delete player D
##curl http://localhost:5003/players/s -X DELETE

# get all players
curl http://localhost:5003/players  -X GET
