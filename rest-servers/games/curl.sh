

# format non REST
# export TOKEN (into ACCESS)
#curl http://localhost:5001/login -H "Content-Type: application/json" -d '{"user_name":"Tartempion", "password":"Tartempion"}' -X POST

ACCESS="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDMxODQyMDUsIm5iZiI6MTYwMzE4NDIwNSwianRpIjoiMDRhZGM1NmItNzI3NS00YzU3LTkxNDQtYzI5MDc3MTRlZWFmIiwiZXhwIjoxNjAzMTg1MTA1LCJpZGVudGl0eSI6IlRhcnRlbXBpb24iLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.I-5L-VGfILqQPopxmjDH80g2sQfXidxUifPP-GrtH3w"

#echo "ACCESS=$ACCESS"

#create a game 
curl http://localhost:5004/games -d 'name=Raspoutine&description=test&variant=standard&archive=0&anonymous=0&silent=0&cumulate=0&fast=0&speed_moves=2&speed_retreats=1&speed_adjustments=1&play_weekend=0&manual=0&access_code=0&access_restriction_reliability=0&access_restriction_regularity=0&access_restriction_performance=0&nb_max_cycles_to_play=500' -H "Authorization: Bearer $ACCESS" -X POST

# get data of a game R
#curl http://localhost:5004/games/Tartempion

# update data a game U
#curl http://localhost:5004/games -d 'name=Tartempion&current_state=2' -X PUT

# delete game D
#curl http://localhost:5004/games/Tartempion2 -X DELETE

# get all games
#curl http://localhost:5004/games  -X GET

# create a pairing
#curl http://localhost:5004/pairings -d 'game_id=1&player_id=1' -X POST

# delete pairing
#curl http://localhost:5004/pairings -d 'game_id=1&player_id=1' -X DELETE

# get all pairing
#curl http://localhost:5004/pairings  -X GET
