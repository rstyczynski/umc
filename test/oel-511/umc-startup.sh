source ~/umc/bin/umc.h &>/dev/null

if [ $? != 0 ]; then 
	echo ''
	echo 'Error setting up umc, see below the details:' 
	source $HOME/umc/bin/umc.h 
	echo '' 
else 
	umc
fi
