w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)
cp $1 $1.framed
# left
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,0 0,$(expr $h - 1)" $1.framed
# right
convert $1.framed -strokewidth 1 -stroke black -draw "line $(expr $w - 1),0 $(expr $w - 1),$(expr $h - 1)" $1.framed
# top
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,0 $(expr $w - 1), 0" $1.framed
# down
convert $1.framed -strokewidth 1 -stroke black -draw "line 0,$(expr $h - 1) $(expr $w - 1), $(expr $h - 1)" $1.framed
