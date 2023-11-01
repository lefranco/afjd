w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)
echo "width=$w"
echo "heigh=$h"
cp $1 $1.orig

# target : width = 200

ratio=$(( (200 * 100) / $w ))
echo $ratio

convert $1.orig -resize ${ratio}% $1
