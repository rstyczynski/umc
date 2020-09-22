#!/bin/bash

#---
#--- Library
#---

umc_version=0.2

export umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

export toolsBin=$umcRoot/bin

PATH=$PATH:/sbin:$toolsBin

if [ -z "$status_root" ]; then
  export status_root=~/obd
fi

#---------------------------------------------------------------------------------------
#--- call cfg scripts
#---------------------------------------------------------------------------------------
# mandatory paramters
export CSVdelimiter=','

#
# configure umc
#

# 1. load configuration from binary distribution - default values
. $umcRoot/etc/umc.conf

# 2. load configuration from /etc
if [ -f /etc/umc/umc.conf ]; then
  . /etc/umc/umc.conf 
fi

# 3. configure user params
if [ -f ~/.umc/umc.conf ]; then
  . ~/.umc/umc.conf
fi

# 4. configure global params - global params overwrite  
. $toolsBin/global.conf


#prepare secret directory
if [ ! -d ~/.umc ]; then
    mkdir ~/.umc 
fi

if [ $(stat -c %a ~/.umc) != "700" ]; then
   chmod 700 ~/.umc 
fi

#
#
#
declare -A tool_dir_cache

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
    cp -R $umcRoot/varia/pyyaml . >/dev/null 2>&1
    cd pyyaml
    python setup.py install --user >/dev/null 2>&1
    cd ..
    rm -rf pyyaml
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
    cat $toolsBin/global.conf | grep "_layer=" | cut -f1 -d'=' | cut -f2 -d' ' | cut -f1 -d'_'
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
        
        sensor_info)
            unset probeInfo
            invoke $sensor 1 1 >/dev/null 2>&1
            echo $probeInfo
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
	    . $toolsBin/cluster.h

            # fix arguments for subcommands
	    cfgCluster $1
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
  layer_version_detailed=$(eval "echo $(echo \$$layer\_version_detailed)")

  if [ ! "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific/$layer_version_detailed" = "$layer/////" ]; then
    layer_dir="$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific/$layer_version_detailed"
    # if [ -d $umcRoot/tools/$layer_dir ]; then
      echo $layer_dir
    # fi
  fi

  if [ ! "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific" = "$layer////" ]; then
    layer_dir="$layer/$layer_version_major/$layer_version_minor/$layer_version_patch/$layer_version_specific"
    # if [ -d $umcRoot/tools/$layer_dir ]; then
      echo $layer_dir
    # fi
  fi
  if [ ! "$layer/$layer_version_major/$layer_version_minor/$layer_version_patch" = "$layer///" ]; then
    layer_dir="$layer/$layer_version_major/$layer_version_minor/$layer_version_patch"
    # if [ -d $umcRoot/tools/$layer_dir ]; then
      echo $layer_dir
    # fi
  fi
  if [ ! "$layer/$layer_version_major/$layer_version_minor" = "$layer//" ]; then
    layer_dir="$layer/$layer_version_major/$layer_version_minor"
    # if [ -d $umcRoot/tools/$layer_dir ]; then
      echo $layer_dir
    # fi
  fi
  if [ ! "$layer/$layer_version_major" = "$layer/" ]; then
    layer_dir="$layer/$layer_version_major"
    # if [ -d $umcRoot/tools/$layer_dir ]; then
      echo $layer_dir
    # fi
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
                                #echo -n "$umcRoot/tools"
                                #echo $directoryRoot/$directoryLinux/$directoryJava/$directoryWLS/$directorySOA

                                tool_dir=$umcRoot/tools/$directoryRoot/$directoryLinux/$directoryJava/$directoryWLS/$directorySOA
                                if [ -d $tool_dir ]; then
                                  echo $tool_dir
                                fi

                            done
                            for directoryOSB in $(getLayerDirectories osb); do
                                # echo -n "$umcRoot/tools"
                                # echo $directoryRoot/$directoryLinux/$directoryJava/$directoryWLS/$directoryOSB
                                tool_dir=$umcRoot/tools/$directoryRoot/$directoryLinux/$directoryJava/$directoryWLS/$directoryOSB
                                if [ -d $tool_dir ]; then
                                  echo $tool_dir
                                fi
                            done
			else
                            # echo -n "$umcRoot/tools"
                            # echo $directoryRoot/$directoryLinux/$directoryJava/$directoryWLS
                            tool_dir=$umcRoot/tools/$directoryRoot/$directoryLinux/$directoryJava/$directoryWLS
                            if [ -d $tool_dir ]; then
                              echo $tool_dir
                            fi
                        fi
                    done
                else
                    # echo -n "$umcRoot/tools"
                    # echo $directoryRoot/$directoryLinux/$directoryJava
                    tool_dir=$umcRoot/tools/$directoryRoot/$directoryLinux/$directoryJava
                    if [ -d $tool_dir ]; then
                      echo $tool_dir
                    fi
                fi
            done
        else
            # echo -n "$umcRoot/tools"
            # echo $directoryRoot/$directoryLinux
            tool_dir=$umcRoot/tools/$directoryRoot/$directoryLinux
            if [ -d $tool_dir ]; then
              echo $tool_dir
            fi
        fi
      done
    done
}

function locateToolExecDir {
  cmd=$1
  cmd_layer=$(eval "echo $(echo \$$cmd\_layer)")
  cmd_package=$(eval "echo $(echo \$$cmd\_package)")
  
  unset toolExecDir

  if [ ! -z ${tool_dir_cache[$cmd]} ]; then
    toolExecDir=${tool_dir_cache[$cmd]}
  else
  
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

    tool_dir_cache[$cmd]=$toolExecDir
  fi
}


function cfgInfoFile {

  # reset all env settings
  unset UMC_PROBE_META_EXT
  unset UMC_SENSOR_HELP

  unset UMC_PROBE_ARGS
  declare -A UMC_PROBE_ARGS
  
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

  # remote collection?
  if [ ! -z "$umc_remote_system" ]; then
    system_name=$umc_remote_system
  else
    system_name=$(hostname)
  fi

  #run the tool
  if [ "$loop" = "external" ]; then
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ] ; then
        $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $timestampDirective $@
    else
        $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $@ \
        | perl -ne "$perlBUFFER; print \"$system_name,$cmd,\$_\";" \
        | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
    fi
  elif [ "$loop" = "options" ]; then
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ]; then
        $toolExecDir/$cmd $loop_options $timestampDirective $@
    else
        $toolExecDir/$cmd $loop_options $@ \
        | perl -ne "$perlBUFFER; print \"$system_name,$cmd,\$_\";" \
        | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
    fi
  else
    if [ "$timestampMethod" = "internal" ] || [ "$headerMethod" = "internal" ]; then
	$toolExecDir/$cmd $timestampDirective $@ 
    else
	 $toolExecDir/$cmd $@ \
         | perl -ne "$perlBUFFER; print \"$system_name,$cmd,\$_\";" \
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
  unset UMC_PROBE_META_EXT # to keep info in another file - used in wls probe
  unset UMC_SENSOR_HELP

  unset UMC_SENSOR_ARGS # map with arg
  declare -a UMC_SENSOR_ARGS

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
  
  if [ "$rawHeaderMethod" = "line" ]; then
    systemHeader=$($toolCmd | sed -n "$rawHeaderDirective"p)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  
  if [ "$rawHeaderMethod" = "command" ]; then
    systemHeader=$(eval $rawHeaderDirective)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi

  if [ "$rawHeaderMethod" = "bash" ]; then
    systemHeader=$(. $toolExecDir/$rawHeaderDirective)
    if [ "$rawHeader" = "$systemHeader" ]; then
      echo OK
      #reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  
  if [ "$rawHeaderMethod" = "script" ]; then
    systemHeader=$($toolExecDir/$rawHeaderDirective | tr -d '\r')
    if [ "$rawHeader" = "$systemHeader" ]; then
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


echo Universal Metrics Collector initialized.

