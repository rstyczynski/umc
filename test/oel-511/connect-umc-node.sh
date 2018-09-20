#!/bin/bash

name=$1

docker exec -it umc-$name /bin/bash -l
