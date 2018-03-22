#!/bin/bash

  if [ "$DEBUG" = "" ]; then DEBUG=0; fi
  if [ -z $1 ]; then
     echo Can not continue for pid:$1
  else
      if [ $DEBUG -eq 1 ]; then
       echo killtree started for: $1
     fi
      pid=$1
      if [ -z "$2" ]; then 
        depth=0
        allChildren=$pid
      else
        depth=$2
      fi
      if [ $depth -eq 0 ]; then
        #! it returns just $pid !!! :)
	case $(uname) in
	SunOS)
        	allChildren=$(ps -eo pid,ppid,pid | grep "^ *$pid " | sed 's/^ *//g' | cut -d' ' -f1)
		;;
	*)
        	allChildren=$(ps -eo pid,ppid,pid | grep "^\s*$pid " | sed 's/^\s*//g' | cut -d' ' -f1)
		;;
	esac
      fi
      kill[$depth]=$3

       #list processes started by $pid
       #grep "\s*$pid" does not work in osx :( space must be used instead, but it does not work in linux
	case $(uname) in
	SunOS)
       		children[$depth]=$(ps -eo pid,ppid,pid | grep " $pid " | grep -v grep | grep -v "^ *$pid" | sed 's/^ *//g' | tr -s ' ' | cut -d' ' -f1)
 		;;
	*)
       		children[$depth]=$(ps -eo pid,ppid,pid | grep " $pid " | grep -v grep | grep -v "^\s*$pid" | sed 's/^\s*//g' | tr -s ' ' | cut -d' ' -f1)
 		;;
	esac

      allChildren="$allChildren ${children[$depth]}"
      if [ $DEBUG -eq 1 ]; then
        echo pid: $pid
        echo depth=$depth
        echo children at $depth: ${children[$depth]}
      fi
       for child in ${children[$depth]}; do
         if [ $DEBUG -eq 1 ]; then 
           echo child: $child
         fi
          kill=${kill[$depth]}
          depth=$(( $depth + 1 ))
          . $toolsBin/killtree.sh "$child" "$depth" "$kill" >/dev/null
          depth=$(( $depth - 1 ))
       done
       if [ $DEBUG -eq 1 ]; then
         echo exit:
         echo depth=$depth
         echo children at $depth: ${children[$depth]}
        echo kill:${kill[$depth]}
       fi
      
      if [ $depth -eq 0 ] && [ "${kill[$depth]}" != "NO" ]; then
         kill -9 $allChildren 2>&1  >/dev/null 
         allChildren=""
      fi
      echo $allChildren
  fi
  #rm $1.*

