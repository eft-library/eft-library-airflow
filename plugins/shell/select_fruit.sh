FRUIT=$1
if [ $FRUIT == APPLE ]; then
	echo "Apple"
elif [ $FRUIT == ORANGE ]; then
	echo "Orange"
elif [ $FRUIT == GRAPE ]; then
	echo "Grape"
else
	echo "Other"
fi
