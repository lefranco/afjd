#!/bin/bash


echo "------------------------------"
echo "check users"
curl -s https://users.diplomania.fr/login -H "Content-Type: application/json" -d '{"user_name":"one", "password":"one"}' -X  POST

echo "------------------------------"
echo "check players"
curl -s https://players.diplomania.fr/events -X GET 

echo "------------------------------"
echo "check games + its database"
curl -s https://games.diplomania.fr/tournaments -X GET

echo "------------------------------"
echo "check emails"
curl -s https://emails.diplomania.fr/send-email-simple -H "Content-Type: application/json" -d '{"subject":"test", "body":"test", "email":"jeremie.lefrancois@gmail.com"}' -X POST

echo "------------------------------"
echo "check solver"
curl -s https://solver.diplomania.fr/command -H "Content-Type: application/json" -d '{"command":"ls"}' -X POST
