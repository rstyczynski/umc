##
## Start params and sequence
##

TESTID=A
DURATION=1
DURATION_BASE=3600
INTERVAL_OS=5
INTERVAL_WLS=30
 
cfgCluster
copyCfg
measureLinux
measureSOA
measureOSB
 
 
##
## Stop params and sequence
##

stopMeasurements
getDataFiles


