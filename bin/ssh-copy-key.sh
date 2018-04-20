#!/bin/bash
umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

port=22
if [ "$1" == "-p" ]; then
  port=$2
  shift;shift
fi
servers=$1
user=$(whoami)

read -p "Enter password:" -s pwd

for server in $servers; do
  expect $umcRoot/bin/ssh-copy-key.exp $port $user@$server $pwd
done
