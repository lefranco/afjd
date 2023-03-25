#!/usr/bin/env bash


# compiles
# must allow commands : change ALLOW_COMMAND = True in server.py beforehand

curl https://solver.diplomania.fr:443/command -d 'cmd=cd engine; make' -X POST
