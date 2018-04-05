#!/bin/bash

delay=$1
count=$2
tools=$3
shift; shift; shift

logDir=.
blocking=1

trap stopStats SIGHUP SIGINT SIGTERM

function stopStats {
	status=stopping

    echo
	echo UMC batch collector stopped by user.
	#--- stop processes
	
    for job in $(jobs | cut -f1 -d']' | cut -f2 -d'['); do
        kill %$job
    done
	exit 2
}

#
# Taking args w/o getops from: https://gist.github.com/dgoguerra/9206418
#
while [ "$#" -gt 0 ]
do  
    option=$(echo $1 | cut -f1 -d'=')
    arg=$(echo $1 | cut -f2 -d'=')
	case "$option" in
    --testId)
		testId=$arg
		;;
    --logDir)
		logDir=$arg
		;;
    --nonblocking)
		blocking=0
		;;
	--)
		break
		;;
	# an option argument, continue
	*)	;;
	esac
	shift
done

umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
. $umcRoot/bin/umc.h
echo

echo "Batch UMC collector initializes data collection for following probes:"
echo $tools | tr ' ' '\n' | tr ':' ' ' | sed 's/^/-> /g'
echo

for tool in $tools; do
    cmd=$(echo $tool | cut -f1 -d':')
    args=$(echo $tool | cut -f2-999 -d':')
    if [ $args = $cmd ]; then
        unset args  
    fi
    echo Starting umc $cmd collect $count $delay $args ...
    
    # Get subsystem name from probe. 
    # As it's a proble internal thing how to interpret options need to use setenv logic.
    
    # A. locate the tool
    locateToolExecDir $cmd
    
    # B. call setenv logic and extract subsystem name
    if [ -f $toolExecDir/$cmd.setenv ]; then
        . $toolExecDir/$cmd.setenv collect $count $delay $args 
    fi
    if [ ! -z "$UMC_PROBE_LOG_NAME" ]; then
        subsystem_name=$cmd\_$UMC_PROBE_LOG_NAME
    else
        subsystem_name=$cmd
    fi
    
    if [ ! -d $logDir/$testId ]; then
        mkdir -p $logDir/$testId
    fi
    # execute
    umc $cmd collect $delay $count $args | perl $umcRoot/bin/logdirector.pl -dir $logDir/$testId -n $subsystem_name -rotateByTime clock -timeLimit 900 -addDateSubDir -alwaysRotate -prefixDate -detectHeader & 
    
    # clean
    unset UMC_PROBE_LOG_NAME
    unset subsystem_name
    unset cmd
    unset args
done

echo

if [ $blocking -eq 1 ]; then
    echo "Waiting for probes to finish data collection."
    while [ $count -gt 0 ]; do
        echo -n $count,
        sleep $delay
        count=$(( $count - 1 ))
    done
    echo done.
    echo
    echo It may take few more seconds to finalize...
    wait
    exit 0
else
    echo "Probes left running in background. Use umc_stopAll.sh to stop."
    exit 1
fi

