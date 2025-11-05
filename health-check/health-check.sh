#!/bin/bash


echo "------------------------------"
echo "check users"
curl -s https://users.diplomania2.fr/login -H "Content-Type: application/json" -d '{"user_name":"one", "password":"one"}' -X  POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check players"
curl -s https://players.diplomania2.fr/events -X GET  --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check games + its database"
curl -s https://games.diplomania2.fr/tournaments -X GET --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check emails"
curl -s https://emails.diplomania2.fr/send-email-simple -H "Content-Type: application/json" -d '{"subject":"test", "body":"test", "email":"jeremie.lefrancois@gmail.com"}' -X POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check solver"
curl -s https://solver.diplomania2.fr/command -H "Content-Type: application/json" -d '{"command":"ls"}' -X POST --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

echo "------------------------------"
echo "check scheduler"
curl -s https://scheduler.diplomania2.fr/access-logs/10 -X GET --connect-timeout 5
if [ $? -ne 0 ]; then echo "Failed !" ; fi

