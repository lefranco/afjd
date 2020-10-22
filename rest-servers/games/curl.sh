

# format non REST
# get TOKEN
#curl http://localhost:5001/login -H "Content-Type: application/json" -d '{"user_name":"two", "password":"two"}' -X POST

# get from reply
ACCESS=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDMzNzkwMDUsIm5iZiI6MTYwMzM3OTAwNSwianRpIjoiNzJiNTg3ZDEtYTUzNS00Yjc4LWIyZDgtMGQ5ZTBjN2QyY2Q2IiwiZXhwIjoxNjAzMzc5OTA1LCJpZGVudGl0eSI6InR3byIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.-8ghYrZETqKixnWxIeXN13idYlkzxfvo_oqCMxxcJdM

#create a game 
#curl http://localhost:5004/games  -H "access_token: $ACCESS" -d 'name=Raspoutine&description=test&variant=standard&archive=0&anonymous=0&silent=0&cumulate=0&fast=0&speed_moves=2&speed_retreats=1&speed_adjustments=1&play_weekend=0&manual=0&access_code=0&access_restriction_reliability=0&access_restriction_regularity=0&access_restriction_performance=0&nb_max_cycles_to_play=500&pseudo=Tartempion' -X POST


# create a pairing
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=1&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=2&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=3&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=4&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=5&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=6&pseudo=Tartempion' -X POST
#curl http://localhost:5004/allocations -H "access_token: $ACCESS" -d 'game_id=3&player_id=7&pseudo=Tartempion' -X POST

# start game
#curl http://localhost:5004/games/Raspoutine -H "access_token: $ACCESS" -d 'current_state=1&pseudo=Tartempion' -X PUT




# submit orders
#curl http://localhost:5004/game-orders/3 -H "access_token: $ACCESS" -d 'names={"roles":{"0":["Arbitre","Arbitre","M"],"1":["Angleterre","anglais","E"],"2":["France","francais","F"],"3":["Allemagne","allemand","G"],"4":["Italie","italien","I"],"5":["Autriche","autrichien","A"],"6":["Russie","russe","R"],"7":["Turquie","turc","T"]},"zones":{"1":"ADR","2":"AEG","3":"alb","4":"ank","5":"apu","6":"arm","7":"BAL","8":"BAR","9":"bel","10":"ber","11":"BLA","12":"boh","13":"BOT","14":"bre","15":"bud","16":"bul","17":"bur","18":"cly","19":"con","20":"den","21":"EAS","22":"edi","23":"ENG","24":"fin","25":"gal","26":"gas","27":"GOL","28":"gre","29":"HEL","30":"hol","31":"ION","32":"IRI","33":"kie","34":"lon","35":"lvn","36":"lvp","37":"mar","38":"MID","39":"mos","40":"mun","41":"naf","42":"nap","43":"NAT","44":"NRG","45":"NTH","46":"nwy","47":"par","48":"pic","49":"pie","50":"por","51":"pru","52":"rom","53":"ruh","54":"rum","55":"ser","56":"sev","57":"sil","58":"SKA","59":"smy","60":"spa","61":"stp","62":"swe","63":"syr","64":"tri","65":"tun","66":"tus","67":"TYN","68":"tyr","69":"ukr","70":"ven","71":"vie","72":"wal","73":"war","74":"WES","75":"yor","76":"","77":"","78":"","79":"","80":"","81":""},"coasts":{"1":"ec","2":"nc","3":"sc"}}&orders=[{"order_type":1,"active_unit":{"type_unit":2,"role":3,"zone":20},"destination_zone":62},{"order_type":1,"active_unit":{"type_unit":1,"role":3,"zone":51},"destination_zone":35},{"order_type":4,"active_unit":{"type_unit":1,"role":3,"zone":12}}]&role_id=3&pseudo=two' -X POST

# ask adjudication
#curl http://localhost:5004/game-adjudications/3 -H "access_token: $ACCESS" -d 'names={"roles":{"0":["Arbitre","Arbitre","M"],"1":["Angleterre","anglais","E"],"2":["France","francais","F"],"3":["Allemagne","allemand","G"],"4":["Italie","italien","I"],"5":["Autriche","autrichien","A"],"6":["Russie","russe","R"],"7":["Turquie","turc","T"]},"zones":{"1":"ADR","2":"AEG","3":"alb","4":"ank","5":"apu","6":"arm","7":"BAL","8":"BAR","9":"bel","10":"ber","11":"BLA","12":"boh","13":"BOT","14":"bre","15":"bud","16":"bul","17":"bur","18":"cly","19":"con","20":"den","21":"EAS","22":"edi","23":"ENG","24":"fin","25":"gal","26":"gas","27":"GOL","28":"gre","29":"HEL","30":"hol","31":"ION","32":"IRI","33":"kie","34":"lon","35":"lvn","36":"lvp","37":"mar","38":"MID","39":"mos","40":"mun","41":"naf","42":"nap","43":"NAT","44":"NRG","45":"NTH","46":"nwy","47":"par","48":"pic","49":"pie","50":"por","51":"pru","52":"rom","53":"ruh","54":"rum","55":"ser","56":"sev","57":"sil","58":"SKA","59":"smy","60":"spa","61":"stp","62":"swe","63":"syr","64":"tri","65":"tun","66":"tus","67":"TYN","68":"tyr","69":"ukr","70":"ven","71":"vie","72":"wal","73":"war","74":"WES","75":"yor","76":"","77":"","78":"","79":"","80":"","81":""},"coasts":{"1":"ec","2":"nc","3":"sc"}}&pseudo=Tartempion' -X POST

# post message
#curl http://localhost:5004/game-messages/3 -H "access_token: $ACCESS" -d 'role_id=6&dest_role_id=3&content=Time for attack&pseudo=one' -X POST

# get messages
#curl http://localhost:5004/game-messages/3 -H "access_token: $ACCESS" -d 'role_id=3&pseudo=two' -X GET

# post declaration
#curl http://localhost:5004/game-declarations/3 -H "access_token: $ACCESS" -d 'role_id=6&content=Hello world&pseudo=one' -X POST

# get declarations
#curl http://localhost:5004/game-declarations/3 -H "access_token: $ACCESS" -d 'role_id=6&pseudo=one' -X GET

