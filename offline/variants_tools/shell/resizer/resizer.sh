#!/bin/bash

echo "Resize picture with scale"

if [ -z $1 ] ; then
    echo "Missing argument 1 file name"
    exit
fi

if [ ! -f $1 ] ; then
    echo "File $1 does not exist"
    exit
fi

if [ -z $2 ] ; then
    echo "Missing argument 2 scale (in percent)"
    exit
fi

w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)
echo "Before"
echo "width=$w"
echo "heigh=$h"

ratio=$2

convert $1 -resize ${ratio}% $1.scaled

w=$(convert $1.scaled -format "%[w]" info:)
h=$(convert $1.scaled -format "%[h]" info:)

echo "After"
echo "width=$w"
echo "heigh=$h"
