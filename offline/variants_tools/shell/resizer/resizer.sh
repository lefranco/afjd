w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)
echo "Before"
echo "width=$w"
echo "heigh=$h"
cp $1 $1.orig

# target  width 
TARGET_WIDTH=100


ratio=$(( ($TARGET_WIDTH * 100) / $w ))
echo $ratio

convert $1.orig -resize ${ratio}% $1

w=$(convert $1 -format "%[w]" info:)
h=$(convert $1 -format "%[h]" info:)

echo "After"
echo "width=$w"
echo "heigh=$h"
