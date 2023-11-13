#!/bin/bash


echo "------------------------------"
echo "check users"
curl https://users.diplomania.fr/login -H "Content-Type: application/json" -d '{"user_name":"one", "password":"one"}' -X  POST

echo "------------------------------"
echo "check players"
curl https://players.diplomania.fr/site_image -X GET | cut -d, -f 1

echo "------------------------------"
echo "check games + its database"
curl https://games.diplomania.fr/tournaments -X GET

echo "------------------------------"
echo "check emails"
curl https://emails.diplomania.fr/send-email-simple -H "Content-Type: application/json" -d '{"subject":"test", "body":"test", "email":"jeremie.lefrancois@gmail.com"}' -X POST

echo "------------------------------"
echo "check solver"
curl https://solver.diplomania.fr/command -H "Content-Type: application/json" -d '{"command":"ls"}' -X POST
