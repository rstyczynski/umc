#!/bin/bash
# creates umc nodes to test umc
# requires umc-oel511 image

# the script directory
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UMC_HOME=$(cd $scriptDir && cd ../../../umc && pwd -P)   
IMAGE="tomvit/umc-oel511:1.5"

# create umc network
docker network ls | grep umcnet >/dev/null

if [ "$?" -eq 1 ]; then
        echo "* creating umcnet network 192.168.0.0/16"
	docker network create --subnet=192.168.0.0/16 umcnet
fi

create_node() {
  name=$1
  ip=$2
  nostart=$3

  echo "* creating node umc-$name, ip=$ip..."  
  docker kill umc-$name &>/dev/null
  docker rm umc-$name &>/dev/null
  if [ "$nostart" != "nostart" ]; then
    docker run --user oracle --net umcnet -it -h $name -v $UMC_HOME:/home/oracle/umc --name umc-$name --ip $ip -d $IMAGE \
	/bin/bash -l -c 'umcrunnerd --verbose &>/home/oracle/umc/bin/$HOSTNAME.out' 
  else
    docker run --user oracle --net umcnet -it -h $name -v $UMC_HOME:/home/oracle/umc --name umc-$name --ip $ip -d $IMAGE /bin/bash -l
  fi
}

create_node ukbn01hr 192.168.10.101 $1
create_node ukbn02hr 192.168.10.102 $1
create_node ukbn03hr 192.168.10.103 $1

