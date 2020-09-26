

# create a pairing
curl http://localhost:5003/pairings -d 'game_id=1&player_id=1' -X POST

# delete pairing
#curl http://localhost:5003/pairings -d 'game_id=1&player_id=1' -X DELETE

# get all pairing
curl http://localhost:5003/pairings  -X GET
