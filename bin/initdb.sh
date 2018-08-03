#!/bin/bash
# use this script as an example to initialize your influxdb DB
DBNAME="rodmon_vfuk_npp"
USER="rodmon"
PASS="rodmon"

echo "* starting db..."
start-influxd.sh

sleep 1

echo "* creating user '$USER'"
influx -execute "CREATE USER $USER WITH PASSWORD '$PASS' WITH ALL PRIVILEGES"

echo "* stopping db..."
stop-influxd.sh 

echo "* changing the authentication"
# change the authentication
pwd=$(pwd)
cd $(dirname $(which influx))/../../etc/influxdb/
rm -f *.bckp
sed -i.bckp s/^.*auth-enabled.*=.*false/auth-enabled=true/g influxdb.conf
cd $pwd

echo "* starting db..."
start-influxd.sh

sleep 1

echo "* creating db '$DBNAME'"
influx --username '$USER' --password '$PASS' -execute "CREATE DATABASE $DBNAME WITH DURATION INF REPLICATION 1 SHARD DURATION 7d"

