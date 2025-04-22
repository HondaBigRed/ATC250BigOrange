#!/bin/sh
ARCH=$( uname -m )
KERNEL=$( uname -s )
SCRIPT=$0

while [ -h "$SCRIPT" ]; do
	SCRIPT=$( readlink "$SCRIPT" )
done

BASE_PATH="${SCRIPT%/*}"
LAST_PATH="$PWD"

if [ ! -e "$BASE_PATH/TSDash.properties" ]; then
	echo "This script must be located in the TunerDash directory. To be able"
	echo "to launch without path create a symlink of this script to a directory in PATH."
	echo
	echo "Example: ln -s /home/john_doe/EcuDashHub/EcuEashHub.sh /usr/local/bin"
	exit 1
fi

#-Djava.library.path=/root/jre/armhf/lib/arm 
cd "$BASE_PATH" && java -jar TSDash.jar $1
RESULT=$?

if [ -d "$LAST_PATH" ]; then
	cd "$LAST_PATH"
fi

exit $RESULT

