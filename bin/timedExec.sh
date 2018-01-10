#!/bin/bash

if [ "$1" = "" ]; then
	echo Script name must be specified.
	echo 'Usage: timedExec.sh interval count script [param1 param2 ...]' 
	exit 1
fi

interval=$1
executonCnt=$2

export LC_CTYPE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

unset DEBUG
if [ "$3" = "DEBUG" ]; then
	DEBUG=true
	shift
fi

script=$3

function debug {

	if [ $DEBUG ]; then 
		echo $1 >&2
	fi
}


function clean_up {

        if [ $1 -eq 0 ]; then
                debug Done.
        else
                debug "Done with errors."
        fi
        exit $1
}

function stop {
        debug "Warning: Program stopped."
        clean_up 0
}

trap stop SIGHUP SIGINT SIGTERM SIGQUIT SIGSTOP

dsn=$1

while [ $executonCnt -gt 0 ]; do
	$script $4 $5 $6 $7 $8 $9 

	debug "Sleeping $interval second(s) . . ."
	sleep $interval
	let executonCnt-=1
done

clean_up 0

