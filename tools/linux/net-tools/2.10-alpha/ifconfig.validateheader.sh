#!/usr/bin/bash

ifname=$(ifconfig | head -1 | cut -f1 -d':')

ifconfig $ifname | grep X | 
sed 's/RX packets /RX packets:/g'| 
sed 's/TX packets /TX packets:/g'| 
sed 's/RX errors /RX errors:/g'| 
sed 's/TX errors /TX errors:/g'| 
sed 's/bytes /bytes:/g'| 
sed 's/dropped /dropped:/g'| 
sed 's/overruns /overruns:/g'| 
sed 's/frame / frame:/g'| 
sed 's/carrier /carrier:/g'| 
sed 's/collisions /collisions:/g'| 
sed 's/[0-9]//g' | sed 's/(. \w*B)//g' | tr -d ' ' | tr -d '\n'
