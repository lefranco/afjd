#!/bin/bash

python3 server.py $1
if [ $? -ne 0 ] ; then read ; fi

exit
