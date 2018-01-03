#---
#--- Library
#---

if [ -z "$umcRoot" ]; then
  export umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

export toolsBin=$umcRoot/bin

# configure
. $umcRoot/etc/config.h

# ATTENTION!
# Do not use buffered!
# Timestamps added to data rows will contain not correct information. 
# It will be moment of buffer flush not a proper moment of collecting data.
export BUFFERED=no

function decodeVersion {
  system_type=$(uname -s)
  version_full=$(uname -r | cut -d'-' -f1)
  version_specific=$(uname -r | cut -d'-' -f2-999)

  version_major=$(uname -r | cut -d'-' -f1 | cut -d'.' -f1)
  version_minor=$(uname -r | cut -d'-' -f1 | cut -d'.' -f2)
  version_patch=$(uname -r | cut -d'-' -f1 | cut -d'.' -f3)
}

function locateToolExecDir {

  cmd=$1
  cmd_version=$(eval "echo $(echo \$$cmd\_version)")
 
  unset toolExecDir
  if [ -f $umcRoot/tools/$system_type/$version_major/$version_minor/$version_patch/$version_specific/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$system_type/$version_major/$version_minor/$version_patch/$version_specific/$cmd_version 
  elif [ -f $umcRoot/tools/$system_type/$version_major/$version_minor/$version_patch/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$system_type/$version_major/$version_minor/$version_patch/$cmd_version 
  elif [ -f $umcRoot/tools/$system_type/$version_major/$version_minor/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$system_type/$version_major/$version_minor/$cmd_version 
  elif [ -f $umcRoot/tools/$system_type/$version_major/0/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$system_type/$version_major/0/$cmd_version 
  elif [ -f $umcRoot/tools/$system_type/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$system_type/$cmd_version 
  elif [ -f $umcRoot/tools/$cmd_version/$cmd ]; then
    toolExecDir=$umcRoot/tools/$cmd_version 
  else
    echo "Error! Reason: utility not recognized as supported tool."
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

  export cmd=$1
  shift

  #setBuffered or not buffered operation
  cfgBuffered

  #decode current system version 
  decodeVersion

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
     loop=true
     interval=$1
     count=$2
     shift 2
  fi

  #hostname
  hostname=$(hostname)

  #print headers
  export CSVheader=$(cat $umcRoot/etc/global.header | tr -d '\n'; echo -n $CSVdelimiter;  cat $toolExecDir/$cmd.header | tr -d '\n'; echo )
  echo $CSVheader

  #run the tool
  if [ "$loop" = "true" ]; then
    $toolsBin/timedExec.sh $interval $count $uosmcDEBUG $toolExecDir/$cmd $1 $2 $3 $4 \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
  else
    $toolExecDir/$cmd $1 $2 $3 $4 \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER -timedelimiter=" " -delimiter=$CSVdelimiter
  fi
}

function locateCompatibleVersions {
 tools=$1

 if [ -z $tools ]; then
  tools="iostat vmstat ifconfig"
 fi

 rm -f "$umcRoot/tools/$system_type/$version_major/$version_minor/*.Success"
 rm -f "$umcRoot/tools/$system_type/$version_major/$version_minor/*.Failure"
 
 toolCnt=0
 for toolCmd in $tools; do
   locateCompatilbleExecDir $toolCmd
   ((toolCnt ++))
 done

 echo
 echo Summary of compatible versions. 
 cat "$umcRoot/tools/$system_type/$version_major/$version_minor/*.Success" | sort | uniq -c | sort -n -r | egrep "^\s+$toolCnt"
}

function reportCompatibilityResult {
  toolCmd=$1
  result=$2
  version=$3

  #decode current system version 
  decodeVersion

  mkdir -p $umcRoot/tools/$system_type/$version_major/$version_minor

  if [ -f $umcRoot/tools/$system_type/$version_major/$version_minor/$toolCmd.Failure ]; then
    rm $umcRoot/tools/$system_type/$version_major/$version_minor/$toolCmd.Failure 
  fi
  echo $version >> $umcRoot/tools/$system_type/$version_major/$version_minor/$toolCmd.$result
}

function testCompatibility {
  toolCmd=$1
  toolExecDir=$2

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

  #test tool compatibility. The rule is that if header is the same, it ok.
  headerlines=$(cat $toolExecDir/$toolCmd.rawheader | grep 'cfg:line' | cut -d':' -f3)
  if [ ! -z $headerlines ]; then
    systemHeader=$($toolCmd | sed -n "$headerlines"p)
    thisHeader=$(cat $toolExecDir/$toolCmd.rawheader | grep -v 'cfg:')
    if [ "$thisHeader" = "$systemHeader" ]; then
      echo OK
      reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  headerscript=$(cat $toolExecDir/$toolCmd.rawheader | grep 'cfg:script' | cut -d':' -f3)
  if [ ! -z "$headerscript" ]; then
    systemHeader=$(. $toolExecDir/$headerscript)
    thisHeader=$(cat $toolExecDir/$toolCmd.rawheader | grep -v 'cfg:')
    if [ "$thisHeader" = "$systemHeader" ]; then
      echo OK
      reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi
  headerCmd=$(cat $toolExecDir/$toolCmd.rawheader | grep 'cfg:command' | cut -d':' -f3-999)
  if [ ! -z "$headerCmd" ]; then
    systemHeader=$($toolExecDir/$headerCmd)
    thisHeader=$(cat $toolExecDir/$toolCmd.rawheader | grep -v 'cfg:')
    if [ "$thisHeader" = "$systemHeader" ]; then
      echo OK
      reportCompatibilityResult $toolCmd Success $toolExecDir
      return 0
    fi
  fi

  echo "Error! Reason: different header"
  echo "Tested system header: $thisHeader"
  echo "This system header  : $systemHeader"
  reportCompatibilityResult $toolCmd Failure $toolExecDir
  return 1
}

function locateCompatilbleExecDir {

  toolCmd=$1


  echo -n "Locating compatible wrappers for $1 ..."

  #decode current system version 
  decodeVersion

  #decode current system version 
  decodeVersion

  if [ ! -d $umcRoot/tools/$system_type/$version_major ]; then
    echo "Error! Reason: Not found any candidates for major version."
    return 1
  fi

  echo ""
  for version_minor_candidate in $(ls $umcRoot/tools/$system_type/$version_major)
  do
    echo -n "  - "
    testCompatibility $toolCmd $umcRoot/tools/$system_type/$version_major/$version_minor_candidate
  done
}

#---
#--- Test Run
#---
function testRun {
 invoke iostat 1 3
 invoke vmstat 1 3
 invoke ifconfig 1 3
}

echo Universal Metrics Collector initialized.

