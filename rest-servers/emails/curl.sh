
# format non REST
# get TOKEN
#curl https://users.diplomania.fr:443/login -H "Content-Type: application/json" -d '{"user_name":"one", "password":"one", "ip_address" : "192.168.1.1"}' -X POST

# get from reply
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY3MzcyMjM4NSwianRpIjoiM2QxYjZmNmUtMmJkOC00MzRkLTg2NDYtZWY1ZDE5MWY0ZmVhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6Im9uZSIsIm5iZiI6MTY3MzcyMjM4NSwiZXhwIjoxNjc1NDUwMzg1fQ.McsYD0abQk70TpqGzupj38PGnc6T-RXMDdu80dmgTPE"

#send email
#
curl https://emails.diplomania.fr/send-email -H "AccessToken: $TOKEN" -H "Content-Type: application/json" -d '{"subject":"subject","body":"body","addressees":"jeremie.lefrancois@gmail.com,jeremie.lefrancois@orange.fr"}' -X POST

