#!/bin/bash

echo "Draws a frame around picture"

if [ -z $1 ] ; then
    echo "Missing argument 1 file name"
    exit
fi

if [ ! -f $1 ] ; then
    echo "File $1 does not exist"
    exit
fi

w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)

# left
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,0 0,$(expr $h - 1)" $1
# right
convert $1.framed -strokewidth 1 -stroke black -draw "line $(expr $w - 1),0 $(expr $w - 1),$(expr $h - 1)" $1
# top
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,0 $(expr $w - 1), 0" $1
# down
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,$(expr $h - 1) $(expr $w - 1), $(expr $h - 1)" $1

