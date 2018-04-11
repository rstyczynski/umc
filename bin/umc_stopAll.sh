#!/bin/bash
 
filterBy="/umc/"
 
if [ "$umcRoot" ]; then
  pids=$(ps aux | grep -v 'grep' |  grep "$filterBy" | tr -s ' ' | cut -d' ' -f2)
  while [ ! -z "$pids" ]; do
    echo Active processes:
    ps aux | grep -v 'grep' |  grep "$filterBy"
    for pid in $pids; do
       $umcRoot/bin/killtree.sh $pid
       echo "Stopped umc process $pid and all child processes."
    done
    pids=$(ps aux | grep -v 'grep' |  grep "$filterBy" | tr -s ' ' | cut -d' ' -f2)
  done
  echo "All clean."
 
fi
