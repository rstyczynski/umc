# Universal Metric Collector

# Rationale
Operating systems are shipped with various set of tools to get certain system metrics. Moreover the same operating system in different versions may be shipped with toolset giving slightly different output. Some of tools are able to run in a loop for defined time and interval, others can't. In such environment it's not possible to relay on the regular tools, without ensuring that all of them are returning data in expected format, during predefined period with pgiven interval. Such insurance is required when other tools are relaying on data produced by tools - e.g. monitoring layer. 

# Solution
The UMC adds intermediate format of data exchange between toolset and other parts of the system. To be universal and generally available uses comma value separated (CSV) plain text format, where the data is separated by comma. The CVS format is well recognized in the industry - format description may be found in RFC 4180. CVS format makes it possible to transport any type of column formatted information, what is  good enough to share operational metrics of monitored system.

# Potential issues
Sharing data using CSV files generates several problems. Meaning of data in the CVS files may not clear. Files may be too big to transport and process. Rows of data may be not enriched with time and source of data collection. 

# Design decisions
To eliminate problems with recognition of column meaning, UMC takes care to always add first row of CVS file with standard header. 

To eliminate problem of too big files, files may be generated to contain subset of rows e.g. split by time. Each file should however contain first row with header.

To eliminate problem of correlation with time and source, each row contains timestamp, system name, and utility name used to gather data.

To eliminate problems with different version of operating systems and tools, scripts collecting metrics are stored in directury structure with system name and version. Such layout makes is possible to handle Linux, Solaris, WebLogic in different versions using the same toolset. Exemplary directory structure is: Linux/3/11/procps_3.2.8/free.

Note that order of columns may vary. Some columns may be missing. It's not clear on this point if extra columns may be added.


# Example
Regular vmstat command executed on Linux 3.11, responses in a following way:

```bash
vmstat 2 3
procs -----------memory---------- ---swap-- -----io---- --system-- -----cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0 187016 358652 164580 795700    0    0     3     6    2    6  1  0 98  0  0	
 0  0 187016 358528 164580 796068    0    0     0     0  282  393  2  0 98  0  0	
 0  0 187016 358528 164580 796148    0    0     0     8  267  566  1  0 99  0  0	
```

UMC does the same job in the following way:

```bash
umc vmstat collect 2 3
datetime,timezone,timestamp,system,source,ProcessRunQueue, ProcessBlocked, MemSwpd,MemFree,MemBuff,MemCache, SwapReadBlocks,SwapWriteBlocks, IOReadBlocks,IOWriteBlocks, Interrupts,ContextSwitches, CPUuser,CPUsystem,CPUidle,CPUwaitIO,CPUVMStolenTime
2018-02-27 05:59:19,-0800,1519739959,soabpm-vm.site,vmstat,0,0,187016,350988,164948,796648,0,0,0,8,319,517,1,0,99,0,0	
2018-02-27 05:59:21,-0800,1519739961,soabpm-vm.site,vmstat,0,0,187016,350988,164948,796660,0,0,0,0,298,772,1,0,99,0,0	
2018-02-27 05:59:23,-0800,1519739963,soabpm-vm.site,vmstat,0,0,187016,350872,164972,796652,0,0,0,52,312,422,2,0,98,0,0	
```

# Implementation
Universal Collector is written in Bash with some scripts in Python. The package consist of:
1. umc.h - set of routins to handle all required interaction with generaic data sources,
2. set of utilities to handle yaml, text, etc., 
3. umcConfig.h - configuration file,
4. set of sensor wrappers to handle regular utilities,
5. set of sensor meta-information to describe regular utilities.

Sensor wrappers are stored in a directory structure caontainign opearting system or utilities package name, and version. Such layout makes it possible to make UMC compatible with generic tools in variosu versions, generating the same CSV output.

Before execution UMC verifies that wrapper is availabe in reguired version. Ideally UMC should use scripts from highest major version of the operating system. It's not yest imlemented, but but UMC will check compativility of generic version. In case of issues should look for proper scripts in minor version directory.

```bash
$UMCRoot..................................... root directory of UMC
$UMCRoot/bin................................. shared scripts compatible with all os, based on gnu utilities
$UMCRoot/tools............................... directory with top level OS type
$UMCRoot/tools/Linux......................... directory with Linux related files
$UMCRoot/tools/Java.......................... directory with Java related files
$UMCRoot/tools/Java/WLS...................... directory with WebLogic related files
$UMCRoot/tools/Java/WLS/SOA.................. directory with SOA related files
$UMCRoot/tools/Java/WLS/SOA/11/1/1/7.0....... directory with SOA 11.1.1.7.0 related files
$UMCRoot/tools/net-tools/1.60................ directory with net-tools package in version 1.60
$UMCRoot/tools/procps/3.2.8.................. directory with procps package in version 3.2.8
$UMCRoot/tools/systat/9.0.4.................. directory with systat package in version 9.0.4
```

Once located proper version of the wrapper, checks if source tool is available in a system. In case of problems stops with error. In case of success UMC returns data to standard output.

# First time use
To configure UMC one have to edit etc/umc.cfg to provide required information about middleware. 

# Regular use
Before use one have to source umc.h which adds command line functions to Bash environment. Apart of internal things, UMC extends classpath by SOA and OSB jars, and calls Oracle Miffleware environment confguration script.

```bash
. ttMetrics/bin/umc.h 

Universal Metrics Collector initialized.
```

After initialization Bash is extended by `umc` command.

```bash
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
```





Current version supports regular Linux utilities, OSB, and SOA. 

Universal Collector relays on regular OS utilities, which harvested by a data formatter generates data in desired format. To make metric collection compatible with any version of Unix-like operating system, set of utility specifice scripts is shipped with UMC together with required metainformation. Files are stored in durectory structure containing system tyle and version, what enables UMC to operate flawlesly on different platforms and versions.

Each wrapper oover regular utility is shipped with meta-information file, which cotains description of CSV headersXXX



OS specific information is stored in directory representing system type, major and minor version. Tool executor verifies if given utility is present in well known directory name. If not error is returned. 

In the case of missing definition for OS being used, it's possible verify if definitions available for other OS releases are compatible with used system. 

To verify compatibility UMC gets headers from executed utility, and compares it with header valid for other OS version. If header is the same, it's assumed that data produced by the utility is compatible as well.



## vmstat
Let's take a look at implementation of vmstat on Linux 3.11, which is identical to iostat.

Raw header file is used as a fingerprint of OS specific utility. First line of the file contains information which part of the output should be used as a header to compare. For vmstat it's two first lines, thus directive says: cfg:lines:1,2. Internally it's passed to sed command, which takes first two lines from vmstat output. 

```bash
cat $UMCRoot/tools/Linux/3/0/vmstat.rawheader 
cfg:line:1,2
procs -----------memory---------- ---swap-- -----io---- -system-- ----cpu----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa
```

Header file is added always on top of CSV data file. Note that apart from vmstat specific information there is always added set of four columns: date, time, hostname, and utility name.

```bash
cat $UMCRoot/tools/Linux/3/0/vmstat.header 
date,time,system,source,ProcessRunQueue,ProcessBlocked,MemSwpd,MemFree,MemBuff,MemCache,SwapReadBlocks,SwapWriteBlocks,IOReadBlocks,IOWriteBlocks,Interrupts,ContextSwitches,CPUuser,CPUsystem,CPUidle,CPUwaitIO
```

Finally the vmstat invocation wrapper is an executable script formatting vmstat output to reach desired CSV format matching header in vmstat.header file.

```bash
cat $UMCRoot/tools/Linux/3/0/vmstat
#!/bin/bash

delay=$1
count=$2
vmstat -n $delay $count
| sed $sedBUFFER 's/  */,/g;s/^,//;s/,$//' \
| sed -n $sedBUFFER '1,2!p'  \
| sed -n $sedBUFFER '1!p'
#Comments
#1. vmstat -n -> prevents vmstat from printing headers after some number of lines
#2. $sedBuffer - controls adding "-u" option which control buffering. On this stage script should work in unbuffered mode
#3. s/... -> replace spaces to comma; removes first and last comma  
#4. sed -n 1,2 -> remove first two lines - header lines
#5. sed -n 1!p -> remove first line which contains average numbers measured from start of the system
```

The output of vmstat is the following:

```bash
date,time,system,source,ProcessRunQueue,ProcessBlocked,MemSwpd,MemFree,MemBuff,MemCache,SwapReadBlocks,SwapWriteBlocks,IOReadBlocks,IOWriteBlocks,Interrupts,ContextSwitches,CPUuser,CPUsystem,CPUidle,CPUwaitIO
2017-11-07,15:09:30,ubuntu,vmstat,0,0,0,518408,32812,125248,0,0,0,0,40,100,3,1,96,0
2017-11-07,15:09:30,ubuntu,vmstat,1,0,0,518456,32812,125248,0,0,0,0,28,74,0,0,100,0
2017-11-07,15:09:32,ubuntu,vmstat,0,0,0,518440,32812,125248,0,0,0,0,32,79,0,1,99,0
2017-11-07,15:09:32,ubuntu,vmstat,0,0,0,518440,32812,125248,0,0,0,0,23,68,0,1,99,0
```

## ifconfig
Definition of ifconfig utility is more complex, as there is no simple header line and output generated by ifconfig is multiline per single interface.

```bash
ifconfig 
eth0      Link encap:Ethernet  HWaddr 00:1c:42:ec:f5:ce  
          inet addr:10.37.129.5  Bcast:10.37.129.255  Mask:255.255.255.0
          inet6 addr: fdb2:2c26:f4e4:1:9dfb:894e:26ce:3d0/64 Scope:Global
          inet6 addr: fdb2:2c26:f4e4:1:21c:42ff:feec:f5ce/64 Scope:Global
          inet6 addr: fe80::21c:42ff:feec:f5ce/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:152755 errors:0 dropped:0 overruns:0 frame:0
          TX packets:143897 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:10583719 (10.5 MB)  TX bytes:16034794 (16.0 MB)
```

Raw header, used to verify compatibility of ifconfig utility, is based on a script as it's not possible to just take some lines as it was doable with vmstat and iostat. Property file specifying raw header instructs that the script should be used, which will extract header information from executed ifconfig utility to produce output compared with expected header stored in second line.

```bash
cat $UMCRoot/tools/Linux/3/0/ifconfig.rawheader 
cfg:script:ifconfig.validateheader.sh
RXpackets:errors:dropped:overruns:frame:TXpackets:errors:dropped:overruns:carrier:collisions:txqueuelen:RXbytes:TXbytes:
```

Raw header extraction script extracts rows used by CVS data extraction logic, but instead of using numbers from the lines, uses ASCII characters. It's a perfect raw header fingerprint proving compatibility of ifconfig utility. 

```bash
cat $UMCRoot/tools/Linux/3/0/ifconfig.validateheader.sh 
#!/usr/bin/bash

ifname=$(ifconfig | cut -f1 -d' '| head -1)
ifconfig $ifname | grep -i X | sed 's/[0-9]//g' | sed 's/(. \w*B)//g' | tr -d ' ' | tr -d '\n'

Header file for ifconfig output looks following:

cat $UMCRoot/tools/Linux/3/0/ifconfig.header 
date,time,system,source,device,RXpackets,RXerrors,RXdropped,RXoverruns,RXframe,TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier,collisions,txqueuelen,RXbytes,TXbytes

Finally the ifconfig invocation wrapper is an executable script formatting vmstat output to reach desired CSV format matching header in vmstat.header file.

cat $UMCRoot/tools/Linux/3/0/ifconfig
#!/bin/bash

#get interface name
netlist=$1

#if no parameter is specified get data from all interfeces
if [ -z $netlist ]; then
  netlist=ALL
fi

#extract interface names
if [ "$netlist" = "ALL" ]; then 
  netlist=$(ifconfig | grep "^[a-zA-Z]" | cut -d ' ' -f1)
fi

#collect data for each interface
for net in $netlist; do 
   ifconfig $net \
   | grep -i X \
   | perl $toolsBin/joinlines.pl -stop "RX bytes" \
   | sed $sedBUFFER 's/[a-zA-Z:]//g' \
   | sed $sedBUFFER 's/  */,/g' \
   | cut -d',' -f2-6,8-13,14-15,18,21  \
   | perl -ne "$perlBUFFER; print \"$net,\$_\";"
#1. grep -i X -> get rows with "x". It's set of rows in are of our interest
#2. joinlines.pl -> join multiline information into one line. Note that on a third line there is "RX bytes" byte sequence
#3. $sedBUFFER -> control buffering of data. Not used.
#4. s/[a-zA-Z:]//g -> remove all non letters and semi colons
#5. s/  */,/g -> replace spaces with comma
#6. -f2-6,8-13,14-15,18,21 -> selects columns with information
#7. print interface information at beginning of each line.
done
```

The output of ifconfig is the following:

```bash
invoke ifconfig 1 5 eth0
date,time,system,source,device,RXpackets,RXerrors,RXdropped,RXoverruns,RXframe,TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier,collisions,txqueuelen,RXbytes,TXbytes
2017-11-07,16:00:22,ubuntu,ifconfig,eth0,154267,0,0,0,0,144759,0,0,0,0,,0,1000,10711689,16167120
2017-11-07,16:00:22,ubuntu,ifconfig,eth0,154270,0,0,0,0,144762,0,0,0,0,,0,1000,10711887,16167614
2017-11-07,16:00:24,ubuntu,ifconfig,eth0,154273,0,0,0,0,144766,0,0,0,0,,0,1000,10712085,16168182
2017-11-07,16:00:24,ubuntu,ifconfig,eth0,154276,0,0,0,0,144768,0,0,0,0,,0,1000,10712283,16168410
2017-11-07,16:00:26,ubuntu,ifconfig,eth0,154279,0,0,0,0,144771,0,0,0,0,,0,1000,10712481,16168808
```

By default ifconfig does not work in a loop, just presenting current data per invocation. That's correct, and the invocation loop is a special option of each utility, which is recognized and controlled by UMC. Special requriments of each utility are stored in $cmd.properties file. In case of ifconfig the file informs invocation logic that looped invocation must be handled by UMC.

```bash
cat $UMCRoot/tools/Linux/3/0/ifconfig.properties 
loop:external
```

## invoke
Heart of the UMC is an invoke function which takes parameters of utility name, optional debug flag, interval and number of executions. Invoke decodes operating system version, finds proper script directory, controls buffering, checks of utility is installed on the system, controls continuous run, and adds header, timestamp, and hostname.

```bash
function invoke {

  unset DEBUG
  if [ "$1" = "DEBUG" ]; then
        export UMCDEBUG=DEBUG
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
  cat $toolExecDir/$cmd.header

  #run the tool
  if [ "$loop" = "true" ]; then
    $toolsBin/timedExec.sh $interval $count $UMCDEBUG $toolExecDir/$cmd $1 $2 $3 $4 \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER
  else
    $toolExecDir/$cmd $1 $2 $3 $4 \
    | perl -ne "$perlBUFFER; print \"$hostname,$cmd,\$_\";" \
    | $toolsBin/addTimestamp.pl $addTimestampBUFFER
  fi
}
```

## locateCompatibleVersions
For operating systems with not compatible scripts it's possible to execute header tests for all known minor versions for the same major version. Below scripts shows list of compatible versions using three utilities: vmstat, iostat, and ifconfig.

Once executed automatically goes trough all versions, and generates summary report.

```bash
locateCompatibleVersions
Locating compatible wrappers for iostat ...
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/0 with iostat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11 with iostat ...Error! Reason: The tool not found in given directory.
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11.delete with iostat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11x with iostat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/5 with iostat ...OK
Locating compatible wrappers for vmstat ...
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/0 with vmstat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11 with vmstat ...Error! Reason: The tool not found in given directory.
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11.delete with vmstat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11x with vmstat ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/5 with vmstat ...OK
Locating compatible wrappers for ifconfig ...
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/0 with ifconfig ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11 with ifconfig ...Error! Reason: The tool not found in given directory.
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11.delete with ifconfig ...Error! Reason: The tool not found in given directory.
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/11x with ifconfig ...OK
  - Testing compatibility of /home/ubuntu/ttMetrics/tools/Linux/3/5 with ifconfig ...OK

Summary of compatible versions.
      3 /home/ubuntu/ttMetrics/tools/Linux/3/5
      3 /home/ubuntu/ttMetrics/tools/Linux/3/11x
      3 /home/ubuntu/ttMetrics/tools/Linux/3/0
```

Details of the function are presented below.

```bash
function locateCompatibleVersions {
 tools=$1

 if [ -z $tools ]; then
  tools="iostat vmstat ifconfig"
 fi

 rm -f $UMCRoot/tools/$system_type/$version_major/$version_minor/*.Success
 rm -f $UMCRoot/tools/$system_type/$version_major/$version_minor/*.Failure
 
 toolCnt=0
 for toolCmd in $tools; do
   locateCompatilbleExecDir $toolCmd
   ((toolCnt ++))
 done

 echo
 echo Summary of compatible versions. 
 cat $UMCRoot/tools/$system_type/$version_major/$version_minor/*.Success | sort | uniq -c | sort -n -r | egrep "^\s+$toolCnt"
}
```

# Regression
1. fix locateCompatibleVersions after moving tools to utility directory

# TODO Tools
1. Ping
2. Add node column to identify process e.g. WebLogic instance on a host
3. Add long timestamp (raw long value of Linux time) as a generic column
4. Add version information: os, utils

# TODO General
1. Automatically execute test for given OS with '0' level utilities. Once executed stores information in directory that test was passed or failed. Invoke should use this information.
2. Invoke performs header test upon first run to write result to files. During next runs it's verified if test was passed or not.
3. Add "procps version" e.g. free -V to validate comatibility of tools and scripts

# Open issues
1. Are extra columns allowed in CSV file?
2. Recognize data formatting returned by OS tools. Is decimal delimiter a dot or comma?
3. Add data description to fields: scale min, max, logarithmic, delta, data label as e.g. kB, MB/s
4. Add data correlation information
5. Add data hierarchy information to fields e.g. ProcessRunQueue -> cpu.ProcessRunQueue


