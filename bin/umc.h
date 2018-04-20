#---
#--- Library
#---

umc_version=0.2

export umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

export toolsBin=$umcRoot/bin

PATH=$PATH:/sbin:$toolsBin

#---------------------------------------------------------------------------------------
#--- call cfg scripts
#---------------------------------------------------------------------------------------
# configure user params
if [ -f ~/etc/umc.cfg ]; then
    . ~/etc/umc.cfg
else
    . $umcRoot/etc/umc.cfg
fi

# configure global params
. $toolsBin/global.cfg

#prepare secret directory
if [ ! -f ~/.umc ]; then
    mkdir ~/.umc 
    if [ $(stat -c %a) != "700" ]; then
       chmod 700 ~/.umc 
    fi
fi

#---------------------------------------------------------------------------------------
#--- check required python version
#---------------------------------------------------------------------------------------
python_version_major=$(python -V 2>&1 | cut -f2 -d' ' | cut -d'.' -f1)
python_version_minor=$(python -V 2>&1 | cut -f2 -d' ' | cut -d'.' -f2)
python_version_patch=$(python -V 2>&1 | cut -f2 -d' ' | cut -d'.' -f3)

python_version=$(( $(( 1000 * $python_version_major )) + $(( 100 * $python_version_minor)) + $python_version_patch  ))
    
if [ $python_version -lt 2600 ]; then
    echo "Error: you need bython >=2.6 to run umc."
    echo
    echo "Install python in a system or in your home directory. Details here: http://thelazylog.com/install-python-as-local-user-on-linux/"
    return 1
fi
    
#---------------------------------------------------------------------------------------
#--- check required python modules
#---------------------------------------------------------------------------------------
python $toolsBin/checkModule.py yaml
if [ $? -ne 0 ]; then
    echo "Note: pyyaml module not available. Installing in user space..."
    if [ ! -d $umcRoot/varia/pyyaml ]; then
    	echo "Error: Directory $umcRoot/varia/pyyaml does not exist. Have you cloned umc with submodules?"
	return 1
    fi
    oldDir=$PWD
    cd /tmp
    unzip -o $umcRoot/varia/pyyaml-master.zip >/dev/null 2>&1
    cd pyyaml-master
    python setup.py install --user >/dev/null 2>&1
    cd ..
    rm -rf pyyaml-master
    cd $oldDir
fi

#---------------------------------------------------------------------------------------
#--- # ATTENTION!
#--- Do not use buffered!
#--- Timestamps added to data rows will contain not correct information. 
#--- It will be moment of buffer flush not a proper moment of collecting data.
#---------------------------------------------------------------------------------------
export BUFFERED=no

function availableSensors {
    cat $umcRoot/bin/global.cfg | grep "_layer=" | cut -f1 -d'=' | cut -f2 -d' ' | cut -f1 -d'_'
}

function usage {

    cat <<EOF
Universal Metrics Collector. Collects system monitoring data and presents in CSV format.

Usage: umc [sensors|test|help|-V] [SENSOR collect delay count] 

    Sensor commands:
        SENSOR.......sensor to collect data

        collect......collect data
        delay........delay in seconds between data collections
        count........number of data collections

    General commands:
        sensors......list available sensors
        test.........perform simple test

        help.........this help
        -V...........get version information

Example:
    umc free collect 5 2
    datetime,timezone,timestamp,system,source,total,used,free,shared,buffers,cached,usedNoBuffersCache,freePlusBuffersCache,SwapTotal,SwapUsed,SwapFree
    2018-01-11 05:00:55,-0800,1515675655,soabpm-vm.site,free,5607456,5123548,483908,0,24384,1061536,4037628,1569828,4128764,163332,3965432
    2018-01-11 05:01:00,-0800,1515675660,soabpm-vm.site,free,5607456,5134916,472540,0,24400,1062808,4047708,1559748,4128764,163284,3965480

EOF

}

function version {
    cat <<EOF
umc version $umc_version
rstyczynski@gmail.com, https://github.com/rstyczynski/umc
EOF
}

# main wrapper over other methods. User should use this command to use umc
function umc {
    export ALL_ARGS=$@

    if [ -z $1 ]; then
        sensor=none
    else
        sensor=$1; shift
    fi

    if [ $sensor = help -o $sensor = -V -o $sensor = test -o $sensor = sensors -o $sensor = cluster ]; then
        command=$sensor
    else
        command=sensor_$1; shift
        delay=$1; shift
        count=$1; shift
        params=$@
    fi
    
    case $command in
        sensor_help)
            invoke $sensor help
        ;;
        
        sensor_collect)
            invoke $sensor $delay $count $params
        ;;
        
        sensors)
            echo $(availableSensors)
        ;;
        
        test)
            umcTestRun
        ;;
        
        cluster)
            # fix arguments for subcommands
            # currently $1 is $sensor :(
            cfgCluster $sensor
        ;;
        
        -V)
            version
        ;;
        
        help) 
            usage
            return 0
        ;;
        
        *)
            usage
            return 1
        ;;
    esac
}

function cfgCluster {
   clusterName=$1

   # configure user params
   if [ ! -f ~/etc/umc_cluster_$1.cfg ]; then
      echo Error! Cluster configuration does not found!
   else
       . ~/etc/umc_cluster_$1.cfg

       if [ ! -z "$OHS" ]; then
          echo "OHS servers: " $OHS
       else
          echo "OHS not defined."
       fi
       
       if [ ! -z "$SOA" ]; then
            echo "SOA servers: $SOA" 
          
            if [ ! -z "$SOA_ADMIN" ]; then
              echo "SOA_ADMIN admin: $SOA_ADMIN" 
            else
              echo "SOA ADMIN not defined."
            fi

            if [ ! -z "$SOA_ADMIN_URL" ]; then
              echo "SOA_ADMIN_URL admin: $SOA_ADMIN_URL" 
            else
              echo "SOA ADMIN URL not defined."
            fi

            if [ ! -z "$SOA_CFG" ]; then
              echo "SOA CFG: >>>"
              echo "$SOA_CFG"
              echo "<<<"
            else
              echo "SOA CFG not defined."
            fi

       else
          echo "SOA not defined."
       fi

       if [ ! -z "$OSB" ]; then
            echo "OSB servers: $OSB" 

            if [ ! -z "$OSB_ADMIN" ]; then
              echo "OSB_ADMIN admin: $SOA_ADMIN" 
            else
              echo "OSB ADMIN not defined."
            fi

            if [ ! -z "$OSB_ADMIN_URL" ]; then
              echo "OSB_ADMIN_URL admin: $SOA_ADMIN_URL" 
            else
              echo "OSB ADMIN URL not defined."
            fi

            if [ ! -z "$OSB_CFG" ]; then
              echo "OSB_CFG: >>>"
              echo "$OSB_CFG"
              echo "<<<"
            else
              echo "OSB CFG not defined."
            fi

       else
          echo "OSB not defined."
       fi

       if [ ! -z "$TEST" ]; then
          echo "TEST servers: " $OHS
       else
          echo "TEST not defined."
       fi
       
       HOSTS="$OHS $SOA $OSB $TEST"
       
   fi

}

function getLayerDirectories {
  local layer=$1
  
  layer_version_major=$(eval "echo $(echo \$$layer\_version_major)")
  layer_version_minor=$(eval "echo $(echo \$$layer\_version_minor)")
  layer_version_patch=$(eval "echo $(echo \$$layer\_version_patch)")
  layer_version_specific=$(eval "echo $(echo \$$layer\_version_specific)")
  
  if [ ! "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific" = "$layer////" ]; then
    echo "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific"
  fi
  if [ ! "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch" = "$layer///" ]; then
    echo "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch"
  fi
  if [ ! "$layer/$layer_version_major/$layer_version_minor" = "$layer//" ]; then
    echo "$layer/$layer_version_major/$layer_version_minor"
  fi
  if [ ! "$layer/$layer_version_major" = "$layer/" ]; then
    echo "$layer/$layer_version_major"
  fi
  echo "$layer"
  
}

function getDirectories {
  layer=$1
  
  for directoryRoot in ""; do
      for directoryLinux in $(getLayerDirectories linux); do
        if [ ! $layer = "linux" ]; then
            for directoryJava in $(getLayerDirectories java); do
                if [ ! $layer = "java" ]; then
                    for directoryWLS in $(getLayerDirectories wls); do
                        if [ ! $layer = "wls" ]; then
                            for directorySOA in $(getLayerDirectories soa); do
                                echo -n "$umcRoot/tools"
                                echo $directoryRoot/$directoryLinux/$directoryJava/$directoryWLS/$directorySOA
                            done
                        else
                            echo -n "$umcRoot/tools"
                            echo $directoryRoot/$directoryLinux/$directoryJava/$directoryWLS
                        fi
                    done
                else
                    echo -n "$umcRoot/tools"
                    echo $directoryRoot/$directoryLinux/$directoryJava
                fi
            done
        else
            echo -n "$umcRoot/tools"
            echo $directoryRoot/$directoryLinux
        fi
      done
    done
}

function locateToolExecDir {
  cmd=$1
  cmd_layer=$(eval "echo $(echo \$$cmd\_layer)")
  cmd_package=$(eval "echo $(echo \$$cmd\_package)")
  
  unset toolExecDir
  
  directories=$(getDirectories $cmd_layer);
  for directory in $directories; do
    if [ -f $directory/$cmd ]; then
        toolExecDir=$directory
        return 0
    fi
    if [ ! -z $cmd_package ]; then
        if [ -f $directory/$cmd_package/$cmd ]; then
            toolExecDir=$directory/$cmd_package
            return 0
        fi
    fi
  done
 
  if [ -z $toolExecDir ]; then
    echo "Error! Reason: utility not recognized as supported tool."
    echo "Available versions:"
    find $umcRoot/tools -name $cmd -type f | sed 's/^/--- /g'
    echo "Your version:"
    cmd_version=$(eval "echo $(echo \$$cmd\_package)")
    echo "--- $cmd_version"
    return 3
  fi
}


function cfgInfoFile {

  # reset all env settings
  unset UMC_PROBE_META_EXT
  unset UMC_SENSOR_HELP
  
  #configure enronment for tool. *setenv is a part of binaries. It's not a configuration file.
  # e.g. set UMC_SENSOR_HEADER  
  if [ -f $toolExecDir/$cmd.setenv ]; then
    . $toolExecDir/$cmd.setenv $ALL_ARGS
  fi

  if [ -z "$UMC_PROBE_META_EXT" ]; then
    probeInfo=$toolExecDir/$cmd.info
    probeYAMLRoot=$cmd
  else
    probeInfo=$toolExecDir/$cmd\_$UMC_PROBE_META_EXT.info
    probeYAMLRoot=$cmd\_$UMC_PROBE_META_EXT
  fi
}

function assertInvoke {
  toolCmd=$1

  unset availabilityMethod 
  
  cfgInfoFile 

  availabilityMethod=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.availability.method)
  if [ $? -ne 0 ]; then
    availabilityMethod="None"
  fi
  
  if [ "$availabilityMethod" = "None" ]; then
    $toolCmd 2>/dev/null 1>/dev/null
    if [ $? -eq 127 ]; then
      echo "Error! Reason: utility not installed."
      return 2
    fi
  fi

  if [ "$availabilityMethod" = "command" ]; then
    command=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.availability.directive)
    $command 2>/dev/null 1>/dev/null
    if [ $? -eq 127 ]; then
      echo "Error! Reason: utility not installed."
      return 2
    fi
  fi

  if [ "$availabilityMethod" = "file" ]; then
    file=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.availability.directive)
    if [ ! -f $file ]; then
      echo "Error! Reason: data file not available."
      return 2
    fi 
  fi

  if [ "$availabilityMethod" = "env" ]; then
    envVariable=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.availability.directive)
    if [ -z $envVariable ]; then
      echo "Error! Reason: required variable not available."
      return 2
    fi 
  fi

}

function cfgBuffered {

 if [ "$BUFFERED" = "yes" ]; then
   export sedBUFFER=""
   export grepBUFFER=""
   export perlBUFFER=""
   export addTimestampBUFFER=""
   export joinlinesBUFFER=""
  else
   export sedBUFFER="-u"
   export grepBUFFER="--line-buffered"
   export perlBUFFER="\$|=1"
   export addTimestampBUFFER="-notbuffered"
   export joinlinesBUFFER="-notbuffered"
  fi
}

function string2value {
    optionsString=$1

    for element in $optionsString; do
      if [[ $element == '$'* ]]; then
        value=$(eval  echo $element)
        #echo $element, $value
        sedCmd="s#$element#$value#g"
        #echo $sedCmd
        optionsString=$(echo $optionsString | sed "$sedCmd")
      fi
    done
    
    echo $optionsString

}

function invoke {

  unset DEBUG
  if [ "$1" = "DEBUG" ]; then
        export uosmcDEBUG=DEBUG
        shift
  fi

  export cmd=$1
  shift

  #setBuffered or not buffered operation
  cfgBuffered

  #locate tool definition directory
  locateToolExecDir $cmd
  if [ $? -eq 3 ]; then
    return 3
  fi

  #check if tool is installed on this platform
  assertInvoke $cmd
  if [ $? -eq 2 ]; then
    return 2
  fi

  interval=$1
  count=$2
  #check if looping is requited
  unset loop
  
  cfgInfoFile 

  loop=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.loop.method)
  if [ $? -ne 0 ]; then
    loop="None"
  fi
  
  if [ "$loop" = "external" ]; then
        shift 2  
  elif [ "$loop" = "options" ]; then
        shift 2
        loop_string=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.loop.directive)
        #convert strong to values
        loop_options=$(string2value "$loop_string")
  fi


  #hostname
  hostname=$(hostname)


#  # reset all env settings
#  unset UMC_PROBE_META_EXT
#  unset UMC_SENSOR_HELP

#  #configure enronment for tool. *setenv is a part of binaries. It's not a configuration file.
#  # e.g. set UMC_SENSOR_HEADER  
#  if [ -f $toolExecDir/$cmd.setenv ]; then
#    . $toolExecDir/$cmd.setenv $@
#  fi

  #TODO implement proper handler for options
  if [ $interval = "help" ]; then
    $toolExecDir/$cmd $UMC_SENSOR_HELP
    return 1
  fi

  #TODO: move global cfg to YAML
  #global header prefix
  export CSVheader=$(cat $umcRoot/etc/global.header | tr -d '\n')
  CSVheader="$CSVheader$CSVdelimiter"

  # tool header is available in $cmd.info
  headerMethod="$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.header.method)"
   
  if [ "$headerMethod" != "internal" ]; then
  	CSVheader="$CSVheader$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.header)"
  fi
 
  if [ "$headerMethod" != "internal" ]; then
    #TODO pass header to log director
    echo $CSVheader
  fi

  #add timestamp
  timestampMethod=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.timestamp.method)
  if [ $? -eq 0 ]; then
    timestampDirective=$($toolsBin/getCfg.py $probeInfo $probeYAMLRoot.timestamp.directive)
  else
    timestampMethod=external
    timestampDirective=""
  fi

  #run the tool
  if [ "$loop" = "external" ]; then
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ] ; then
        $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $timestampDirective $@
    else
        $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $@ \
        | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
        | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
    fi
  elif [ "$loop" = "options" ]; then
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ]; then
        $toolExecDir/$cmd $loop_options $timestampDirective $@
    else
        $toolExecDir/$cmd $loop_options $@ \
        | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
        | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
    fi
  else
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ]; then
	$toolExecDir/$cmd $timestampDirective $@ 
    else
	 $toolExecDir/$cmd $@ \
         | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
         | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
    fi
  fi
}

function testCompatibility {
  toolCmd=$1
  toolExecDir=$2

  unset thisHeader
  unset systemHeader

  echo -n Testing compatibility of $2 with $1 ...

  #check if tool is installed on this platform
  assertInvoke $1
  if [ $? -eq 2 ]; then
    return 2
  fi

  #check if directory is available
  if [ ! -f $toolExecDir/$toolCmd ]; then
    echo "Error! Reason: The tool not found in given directory."
    return 3
  fi
  
    # reset all env settings
  unset UMC_PROBE_META_EXT
  unset UMC_SENSOR_HELP

  #configure enronment for tool. *setenv is a part of binaries. It's not a configuration file.
  # e.g. set UMC_SENSOR_HEADER  
  if [ -f $toolExecDir/$cmd.setenv ]; then
    . $toolExecDir/$cmd.setenv $@
  fi

  # tool header is available in $cmd.info
  if [ -z "$UMC_PROBE_META_EXT" ]; then
    rawHeaderMethod=$($toolsBin/getCfg.py $toolExecDir/$cmd.info $cmd.rawheader.method)
    rawHeaderDirective=$($toolsBin/getCfg.py $toolExecDir/$cmd.info $cmd.rawheader.directive)
    rawHeader=$($toolsBin/getCfg.py $toolExecDir/$cmd.info $cmd.rawheader.expected)
  else
    rawHeaderDirective=$($toolsBin/getCfg.py $toolExecDir/$cmd\_$UMC_PROBE_META_EXT.info $cmd\_$UMC_PROBE_META_EXT.rawheader.directive)
    rawHeader=$($toolsBin/getCfg.py $toolExecDir/$cmd\_$UMC_PROBE_META_EXT.info $cmd\_$UMC_PROBE_META_EXT.rawheader.expected)
  fi
  
  if [[ "$rawHeaderMethod" == "line" ]]; then
    systemHeader=$($toolCmd | sed -n "$rawHeaderDirective"p)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  
  if [[ "$rawHeaderMethod" == "command" ]]; then
    systemHeader=$(eval $rawHeaderDirective)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi

  if [[ "$rawHeaderMethod" == "bash" ]]; then
    systemHeader=$(. $toolExecDir/$rawHeaderDirective)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  
  if [[ "$rawHeaderMethod" == "script" ]]; then
    systemHeader=$($toolExecDir/$rawHeaderDirective | tr -d '\r')
    if [[ "$rawHeader" = "$systemHeader" ]]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi

  echo "Error! Reason: different header"
  echo "Reported header: $systemHeader"
  echo $systemHeader | hexdump
  echo "Expected header: $rawHeader"
  echo $rawHeader | hexdump
  #reportCompatibilityResult $toolCmd Failure $toolExecDir
  return 1
}


#---
#--- Test Run
#---
function umcTestRun { 
 for cmd in $(availableSensors); do
 #for cmd in vmstat; do
    echo -n $cmd: 
    
    locateToolExecDir $cmd
    testCompatibility $cmd $toolExecDir
    
    invoke $cmd 1 1 >/dev/null
    if [ $? -ne 0 ]; then
        echo Error
        locateToolExecDir $cmd
    fi
 done
}


#
# Cluster functions
# 

function getPassword {

    if [ ! -f ~/.umc/pwd ]; then
        read -p "Enter password:" -s pwd
        echo -n $pwd > ~/.umc/pwd
        unset pwd
        echo
    fi

}

function delPassword {

    if [ ! -f ~/.umc/pwd ]; then
        rm ~/.umc/pwd
    fi

}

function copyCfg {
    #
    # --- Copy configuration to Middleware Admin hosts
    #
    echo "$SOA_CFG" | ssh $SOA_ADMIN "cat >umc/etc/umc.cfg"
    echo "$OSB_CFG" | ssh $OSB_ADMIN "cat >umc/etc/umc.cfg"
}
 

function prepareUMC {
    #
    # --- Change permission to very wide to make oracle user able to use umc files.
    #
    for host in $HOSTS; do

    commandToExecute="
    chmod -R 777 umc
    ls -lh
    "

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
    else
       eval $commandToExecute
    fi

    done
}
 
function measureLinux {
    #
    # --- Linux
    #
    
    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
            
    DURATION_OS=$(( $DURATION * $DURATION_BASE / $INTERVAL_OS ))

    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    mkdir -p /tmp/umc;
    chmod 777 /tmp/umc;
    cd /tmp/umc;
    nohup umc_collectAll.sh $INTERVAL_OS $DURATION_OS \"vmstat
    free
    top
    uptime
    meminfo
    netstattcp
    ifconfig
    iostat\" –nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"
    
    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    done
}
 
 
function measureSOA {
    #
    # --- SOA
    #
    
    if [ -z "$SOA" ]; then
        echo "Error: SOA not configured."
        return 1
    fi
        
    host=$SOA_ADMIN
    DURATION_WLS=$(( $DURATION * $DURATION_BASE / $INTERVAL_WLS ))

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    mkdir -p /tmp/umc;
    chmod 777 /tmp/umc;
    cd /tmp/umc;
    nohup umc_collectAll.sh $INTERVAL_WLS $DURATION_WLS \"wls --subsystem=general --url=$SOA_ADMIN_URL
    wls --subsystem=jmsruntime --url=$SOA_ADMIN_URL
    wls --subsystem=jmsserver --url=$SOA_ADMIN_URL
    wls --subsystem=datasource --url=$SOA_ADMIN_URL
    wls --subsystem=channel --url=$SOA_ADMIN_URL
    soabindings --url=$SOA_ADMIN_URL \" -–nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"

    getPassword

    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi
}
 
 
function measureOSB {
    #
    # --- OSB
    #
    
    if [ -z "$OSB" ]; then
        echo "Error: OSB not configured."
        return 1
    fi
    
    host=$OSB_ADMIN
    DURATION_WLS=$(( $DURATION * $DURATION_BASE / $INTERVAL_WLS ))

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    mkdir -p /tmp/umc;
    chmod 777 /tmp/umc;
    cd /tmp/umc;
    nohup umc_collectAll.sh $INTERVAL_WLS $DURATION_WLS \"wls --subsystem=general --url=$OSB_ADMIN_URL
    wls --subsystem=jmsruntime --url=$OSB_ADMIN_URL
    wls --subsystem=jmsserver --url=$OSB_ADMIN_URL
    wls --subsystem=datasource --url=$OSB_ADMIN_URL 1
    wls --subsystem=channel --url=$OSB_ADMIN_URL1
    businessservice --url=$OSB_ADMIN_URL --metrics_type=SERVICE
    businessservice --url=$OSB_ADMIN_URL --metrics_type=URI
    businessservice --url=$OSB_ADMIN_URL --metrics_type=OPERATION \" -–nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi
}
 
 
function stopMeasurements {
    #
    # --- Stop
    #

    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
        
    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    umc_stopAll.sh;

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    done
}
 
 
function getDataFiles {
    #
    # --- Change permission
    #
    
    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
        
    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    cd /tmp;
    chmod -R 777 umc;
    cd umc
    ls -Rlh

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    done


    #
    # --- tar and copy
    #
    DATE=$(date +"%d-%m-%y")
    mkdir /tmp/umc_archive

    for host in $HOSTS; do

    commandToExecute="bash -c \"

    rm umc*.tar.gz
    tar czf umc\_$TESTID_$DATE\_\$(hostname -s).tar.gz /tmp/umc/$TESTID

    \""

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
      scp $host:umc\_$TESTID_$DATE\_$host.tar.gz /tmp/umc_archive
    else
      cat ~/.umc/pwd | sudo -kS su $(whoami) -c "$commandToExecute"
      cp umc\_$TESTID_$DATE\_$host.tar.gz /tmp/umc_archive
    fi

    done
    chmod -R 777 /tmp/umc_archive
}


echo Universal Metrics Collector initialized.

