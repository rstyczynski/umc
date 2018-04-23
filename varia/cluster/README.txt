##
## Start params and sequence
##

TESTID=TESTxA
DURATION=1
DURATION_BASE=3600
INTERVAL_OS=5
INTERVAL_WLS=30


## 
## Configure env.
## 
umc cluster PPE9

##
## Check ssh connectivity
##
ssh-check-key.sh "$HOSTS"

##
## Prepare config
##
prepareUMC
copyCfg

##
##
##
measureLinux
measureSOA
measureOSB

##
## Stop params and sequence
##

stopMeasurements
getDataFiles
