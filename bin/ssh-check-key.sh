#!/bin/bash
umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

port=22
if [ "$1" == "-p" ]; then
  port=$2
  shift;shift
fi
servers=$1
user=$(whoami)

serversError=''
for server in $servers; do
  echo -n $server...
  ssh -q -oBatchMode=yes -p $port $user@$server "echo OK" 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "Error"
    serversError="$serversError $server"
  fi
done

echo

if [ -z "$serversError" ]; then
    echo All good.
else
    echo "Servers with no key authentication:"
    echo $serversError
    echo
    echo "Distribute keys using command:"
    echo ssh-copy-key.sh -p $port "$serversError"   
fi
