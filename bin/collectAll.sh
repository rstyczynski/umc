#!/bin/bash

delay=$1
count=$2
tools=$3

umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
. $umcRoot/bin/umc.h

echo "Batch UMC collector collects data for following probes:"
echo -n '-> '; echo $tools | tr ' ' '\n' | tr ':' ' '
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
    
    # execute
    umc $cmd collect $count $delay $args | perl $umcRoot/bin/logdirector.pl -n $subsystem_name -rotateByTime clock -timeLimit 5 -addDateSubDir -alwaysRotate -prefixDate -detectHeader & 
    
    # clean
    unset UMC_PROBE_LOG_NAME
    unset subsystem_name
    unset cmd
    unset args
done

echo
echo "Probes left running in background."
jobs

