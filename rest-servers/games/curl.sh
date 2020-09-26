

# create a game C
#curl http://localhost:5003/games -d 'name=Tartempion2&variant=1&anonymous=0&silent=0&fast=1&cumulate=0&archive=0&speed_moves=2&speed_retreats=1&speed_adjustments=1&play_weekend=0&manual=0&access_code=0&access_restriction_performance=0&access_restriction_regularity=0&current_advancement=1&last_advancement_to_play=500&current_state=1' -X POST

# get data of a game R
#curl http://localhost:5003/games/Tartempion

# update data a game U
#curl http://localhost:5003/games -d 'name=Tartempion&current_state=2' -X PUT

# delete game D
#curl http://localhost:5003/games/Tartempion2 -X DELETE

# get all games
curl http://localhost:5003/games  -X GET
