#!/bin/bash


echo "------------------------------"
echo "check users"
curl -s https://users.diplomania.fr/login -H "Content-Type: application/json" -d '{"user_name":"one", "password":"one"}' -X  POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check players"
curl -s https://players.diplomania.fr/events -X GET  --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check games + its database"
curl -s https://games.diplomania.fr/tournaments -X GET --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check emails"
curl -s https://emails.diplomania.fr/send-email-simple -H "Content-Type: application/json" -d '{"subject":"test", "body":"test", "email":"jeremie.lefrancois@gmail.com"}' -X POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check solver"
curl -s https://solver.diplomania.fr/command -H "Content-Type: application/json" -d '{"command":"ls"}' -X POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check scheduler"
curl -s https://scheduler.diplomania.fr/access-logs/10 -X GET --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

