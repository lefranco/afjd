

# create a player C
curl https://afjd3.eu.ngrok.io:443/players -d 'pseudo=Tartempion&password=Tartempion&email=toto@labas.com&telephone=111&first_name=John&family_name=Doe&country=FRA&time_zone=UTC + 1' -X POST

# get data of a player R
#curl https://afjd3.eu.ngrok.io:443/players/Zorglub

# update data a player U
# curl https://afjd3.eu.ngrok.io:443/players -d 'pseudo=Zorglub&email=titi@labas.com' -X PUT


# delete player D
##curl https://afjd3.eu.ngrok.io:443/players/s -X DELETE

# get all players
curl https://afjd3.eu.ngrok.io:443/players  -X GET
