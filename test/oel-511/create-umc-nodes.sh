#!/bin/bash
# creates umc nodes to test umc
# requires umc-oel511 image

# the script directory
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UMC_HOME=$(cd $scriptDir && cd ../../../umc && pwd -P)   
IMAGE="tomvit/umc-oel511:1.7"

# create umc network
docker network ls | grep umcnet >/dev/null

if [ "$?" -eq 1 ]; then
        echo "* creating umcnet network 192.168.0.0/16"
	docker network create --subnet=192.168.0.0/16 umcnet
fi

create_node() {
  name=$1
  ip=$2

  echo "* creating node umc-$name, ip=$ip..."  
  docker kill umc-$name >/dev/null
  docker rm umc-$name >/dev/null

  docker run -it \
	--user oracle \
	--net umcnet \
	-h $name.umc.local \
	-v $UMC_HOME:/home/oracle/umc \
	--name umc-$name \
	--ip $ip -d $IMAGE /bin/bash -l >/dev/null
}

create_umc_node() {
  create_node $1 $2
  if [ "$3" != "nostart" ]; then
    docker exec umc-$1 /bin/bash -l -c "start-umcrunner --verbose"
  fi
}

create_idb_node() {
  create_node $1 $2
  docker exec umc-$1 /bin/bash -l -c "start-influxd.sh"
  docker exec umc-$1 /bin/bash -l -c "influx -execute \"CREATE DATABASE rodmon_sample WITH DURATION INF REPLICATION 1 SHARD DURATION 7d\""
  docker exec umc-$1 /bin/bash -l -c "start-idbpush --verbose"
}

# create umcrunnerd nodes
create_umc_node ukbn01hr 192.168.10.101 $1
create_umc_node ukbn02hr 192.168.10.102 $1
create_umc_node ukbn03hr 192.168.10.103 $1

# create influxdb and idbpush node
create_idb_node ukbn10hr 192.168.10.110
