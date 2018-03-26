#!/bin/bash
# sql-collector.sh run sql-collector.js by using SQLCl tool in a Oracle DB

# generate sql file for sqlcl to execute
# her§edoc did not work very well for sqlcl, there was always a newline 
# generated on execution which was a problem for the purpsoe of this script
tmpfile=".sql-executor-$((1 + RANDOM % 1000)).sql"
echo "script sql-collector.js &1" >$tmpfile
echo "exit" >>$tmpfile

# remove the tmpfile on exit
function cleanup {
	rm $tmpfile
}
trap cleanup EXIT

# run sqlcl
sql -S /nolog @$tmpfile "$*"
