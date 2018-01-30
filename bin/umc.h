#---
#--- Library
#---

umc_version=0.1

if [ -z "$umcRoot" ]; then
  export umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

export toolsBin=$umcRoot/bin

# configure
. $umcRoot/etc/umcConfig.h

# ATTENTION!
# Do not use buffered!
# Timestamps added to data rows will contain not correct information. 
# It will be moment of buffer flush not a proper moment of collecting data.
export BUFFERED=no


function availableSensors {
    cat $umcRoot/etc/umcConfig.h | grep "_layer=" | cut -f1 -d'=' | cut -f2 -d' ' | cut -f1 -d'_'
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
ryszard.styczynski@oracle.com, https://github.com/rstyczynski/tools/tree/master/umc
EOF
}

# main wrapper over other methods. User should use this command to use umc
function umc {
    sensor=$1; shift
    if [ $sensor = help -o $sensor = -V -o $sensor = test -o $sensor = sensors ]; then
        command=$sensor
    else
        command=sensor_$1; shift
        delay=$1; shift
        count=$1; shift
        params=$@
    fi
     
    case $command in
        sensor_help)
            echo TODO help for sensor
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


function assertInvoke {
  toolCmd=$1

  unset availabilityMethod 
  if [ -f $toolExecDir/$toolCmd.properties ]; then 
    availabilityMethod=$(cat $toolExecDir/$toolCmd.properties | grep "availability:" | cut -d':' -f2)
  fi
  if [ -z $availabilityMethod ]; then
    availabilityMethod=default
  fi

  if [ "$availabilityMethod" = "default" ]; then
    $toolCmd 2>/dev/null 1>/dev/null
    if [ $? -eq 127 ]; then
      echo "Error! Reason: utility not installed."
      return 2
    fi
  fi

  if [ "$availabilityMethod" = "command" ]; then
    command=$(cat $toolExecDir/$toolCmd.properties | grep "availability:" | cut -d':' -f3)
    $command 2>/dev/null 1>/dev/null
    if [ $? -eq 127 ]; then
      echo "Error! Reason: utility not installed."
      return 2
    fi
  fi

  if [ "$availabilityMethod" = "file" ]; then
    file=$(cat $toolExecDir/$toolCmd.properties | grep "availability:" | cut -d':' -f3)
    if [ ! -f $file ]; then
      echo "Error! Reason: data file not available."
      return 2
    fi 
  fi

  if [ "$availabilityMethod" = "env" ]; then
    envVariable=$(cat $toolExecDir/$toolCmd.properties | grep "availability:" | cut -d':' -f3)
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

function invoke {

  unset DEBUG
  if [ "$1" = "DEBUG" ]; then
        export uosmcDEBUG=DEBUG
        shift
  fi

  export LC_CTYPE=en_US.UTF-8
  export LC_ALL=en_US.UTF-8

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

  #check if looping is requited
  unset loop
  if [ -f $toolExecDir/$cmd.properties ]; then
    loop=$(cat $toolExecDir/$cmd.properties | grep loop | cut -d':' -f2)
  fi

  if [ "$loop" = "external" ]; then
     interval=$1
     count=$2
     shift 2
  elif [ "$loop" = "options" ]; then
     interval=$1
     count=$2
     shift 2
     loop_options=$(eval echo $(cat $toolExecDir/$cmd.properties | grep loop | cut -d':' -f3))
  fi

  #hostname
  hostname=$(hostname)

  #print headers
  export CSVheader=$(cat $umcRoot/etc/global.header | tr -d '\n'; echo -n $CSVdelimiter;  cat $toolExecDir/$cmd.header | tr -d '\n'; echo )
  echo $CSVheader

  #run the tool
  if [ "$loop" = "external" ]; then
    $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $@ \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
  elif [ "$loop" = "options" ]; then
    $toolExecDir/$cmd $loop_options $@ \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
  else
    $toolExecDir/$cmd $@ \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
  fi
}


#---
#--- Test Run
#---
function umcTestRun { 
 for cmd in $(availableSensors); do
    echo -n $cmd: 
    invoke $cmd 1 1 >/dev/null
    if [ $? -eq 0 ]; then
        echo OK
    else
        echo Error
        locateToolExecDir $cmd
    fi
 done
}

echo Universal Metrics Collector initialized.

