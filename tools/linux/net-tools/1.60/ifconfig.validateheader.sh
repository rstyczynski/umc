#!/usr/bin/bash

ifname=$(ifconfig | cut -f1 -d' '| head -1)
ifconfig $ifname | grep -i X | sed 's/[0-9]//g' | sed 's/(. \w*B)//g' | tr -d ' ' | tr -d '\n'


