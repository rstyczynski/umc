ts=$(echo "$(date "+%Y%m%d%H%M") - ($(date +%M)%15)" | bc)
logfile="$ts/files-$ts.out"
mkdir -p $ts

if [ ! -f $logfile ]; then 
	ssh -i keys/id_rsa_npp.brm pin01@ukbn21hr.dc-dublin.de "find /opt/brm/common*/pin*/7.5/var/perflib/*plog.txt -mmin -10" 2>/dev/null | \
	while read fname; do 
		echo "$fname" >>$logfile
		scp -q -i keys/id_rsa_npp.brm pin01@ukbn21hr.dc-dublin.de:$fname $ts/
	done
fi

