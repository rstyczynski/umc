#!/bin/bash
# use this script as an example to initialize your influxdb DB
DBNAME="rodmon"
USER="rodmon"
PASS="rodmon"

start-influxd.sh 2>&1 >/dev/null

# create user and the password
# this will only work when the influxdb was created and requires no authentication
influx -execute "CREATE USER $USER WITH PASSWORD '$PASS' WITH ALL PRIVILEGES"
influx -execute "CREATE DATABASE $DBNAME WITH DURATION INF REPLICATION 1 SHARD DURATION 7d"

# change the authentication
pwd=$(pwd)
cd $(dirname $(which influx))/../../etc/influxdb/
rm -f *.bckp
sed -i.bckp s/^.*auth-enabled.*=.*false/auth-enabled=true/g influxdb.conf
cd $pwd

# restart the db
stop-influxd.sh 2>&1 >/dev/null
start-influxd.sh 2>&1 >/dev/null
