# Universal Metric Collector
> Now with On Board Diagnostics


# Rationale
Operating systems are shipped with various set of tools to get certain system metrics. Moreover the same operating system in different versions may be shipped with toolset giving slightly different output. Some of tools are able to run in a loop for defined time and interval, others can't. In such environment it's not possible to relay on the regular tools, without ensuring that all of them are returning data in expected format, during predefined period with given interval. Such insurance is required when other tools are relaying on data produced by tools - e.g. monitoring layer. 

# Solution
The UMC adds intermediate format of data exchange between toolset and other parts of the system. To be universal and generally available uses comma value separated (CSV) plain text format, where the data is separated by comma. The CVS format is well recognized in the industry - format description may be found in RFC 4180. CVS format makes it possible to transport any type of column formatted information, what is good enough to share operational metrics of monitored system.

# Potential issues
Sharing data using CSV files generates several problems. Meaning of data in the CVS files may not clear. Files may be too big to transport and process. Rows of data may be not enriched with time and source of data collection. 

# Design decisions
To eliminate problems with recognition of column meaning, UMC takes care to always add first row of CVS file with standard header. 

To eliminate problem of too big files, files may be generated to contain subset of rows e.g. split by time. Each file should however contain first row with header.

To eliminate problem of correlation with time and source, each row contains timestamp, system name, and utility name used to gather data.

To eliminate problems with different version of operating systems and tools, scripts collecting metrics are stored in directory structure with system name and version. Such layout makes is possible to handle Linux, Solaris, WebLogic in different versions using the same toolset. Exemplary directory structure is: Linux/3/11/procps_3.2.8/free.

Note that order of columns may vary. Some columns may be missing. It's not clear on this point if extra columns may be added.


# Example
Regular vmstat command executed on Linux 3.11, responses in a following way:

```
vmstat 2 3

procs -----------memory---------- ---swap-- -----io---- --system-- -----cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0 187016 358652 164580 795700    0    0     3     6    2    6  1  0 98  0  0	
 0  0 187016 358528 164580 796068    0    0     0     0  282  393  2  0 98  0  0	
 0  0 187016 358528 164580 796148    0    0     0     8  267  566  1  0 99  0  0	
```

UMC does the same job in the following way:

```
umc vmstat collect 2 3

datetime,timezone,timestamp,system,source,ProcessRunQueue, ProcessBlocked, MemSwpd,MemFree,MemBuff,MemCache, SwapReadBlocks,SwapWriteBlocks, IOReadBlocks,IOWriteBlocks, Interrupts,ContextSwitches, CPUuser,CPUsystem,CPUidle,CPUwaitIO,CPUVMStolenTime
2018-02-27 05:59:19,-0800,1519739959,soabpm-vm.site,vmstat,0,0,187016,350988,164948,796648,0,0,0,8,319,517,1,0,99,0,0	
2018-02-27 05:59:21,-0800,1519739961,soabpm-vm.site,vmstat,0,0,187016,350988,164948,796660,0,0,0,0,298,772,1,0,99,0,0	
2018-02-27 05:59:23,-0800,1519739963,soabpm-vm.site,vmstat,0,0,187016,350872,164972,796652,0,0,0,52,312,422,2,0,98,0,0	
```

# Implementation
Universal Collector is written in Bash with some scripts in Python. The package consist of:
1. umc.h - set of routines to handle all required interaction with generic data sources,
2. set of utilities to handle yaml, text, etc., 
3. umc.cfg - configuration file,
4. set of sensor wrappers to handle regular utilities,
5. set of sensor meta-information to describe regular utilities.

Sensor wrappers are stored in a directory structure containing operating system or utilities package name, and version. Such layout makes it possible to make UMC compatible with generic tools in various versions, generating the same CSV output.

Before execution UMC verifies that wrapper is available in required version. Ideally UMC should use scripts from highest major version of the operating system. It's not yet implemented, but UMC will check compatibility of generic version. In case of issues should look for proper scripts in minor version directory.

```
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

# Installation
To install UMC in a current directory execute below one-liner. It will create umc directory, get UMC from github, and initialize it.

```bash
mkdir umc; cd umc; curl  -Lk https://github.com/rstyczynski/umc/archive/v0.4.1-beta.tar.gz | tar -xz --strip=1; cd ..; . umc/bin/umc.h
```

Cloning repository is also good idea, as umc changes dynamically. As umc relays on os level utilities installing them during setup is a good idea.

```bash
sudo yum install -y git curl python python-yaml perl locales sysstat net-tools
git clone https://github.com/rstyczynski/umc.git
. umc/bin/umc.h 
```


Now you are ready to use UMC on Linux.

# First time use
Before use one have to source umc.h which adds command line functions to Bash environment. Apart of internal things, UMC extends classpath by SOA and OSB jars, and calls Oracle Middleware environment configuration script.

```
. umc/bin/umc.h 

Universal Metrics Collector initialized.
```

After initialization Bash is extended by `umc` command.

```
umc

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

# List available sensors
To list available probes, execute umc with sensors parameter

```
umc sensors

vmstat free top uptime meminfo tcpext netstattcp ifconfig iostat soabindings businessservice
```

It means that this version of UMC is shipped with wide range of Linux probes, and two probes for SOA: one for OSB, and the other one for Composite.


# Simple test
Availability of probes does not mean that all of them will work. Packages may be missing in the Operating system or system may be host different version of utilities. To validate compatibility of tools UMC does two things: (a) checks general availability with known OS level technique, and calls the utility to get returned headers to compare with signature stored in plugin meat-information. UMC 

```
umc test

vmstat:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with vmstat ...OK
free:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with free ...OK
top:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with top ...OK
uptime:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with uptime ...OK
meminfo:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with meminfo ...OK
tcpext:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with tcpext ...OK
netstattcp:Testing compatibility of /home/oracle/ttMetrics/tools/linux/net-tools/1.60 with netstattcp ...OK
ifconfig:Testing compatibility of /home/oracle/ttMetrics/tools/linux/net-tools/1.60 with ifconfig ...OK
iostat:Testing compatibility of /home/oracle/ttMetrics/tools/linux/systat/9.0.4 with iostat ...OK
soabindings:Testing compatibility of /home/oracle/ttMetrics/tools/linux/java/wls/soa/11/1/1/7.0 with soabindings ...OK
businessservice:Testing compatibility of /home/oracle/ttMetrics/tools/linux/java/wls/soa/11/1/1/7.0 with businessservice ...OK
```

In case of errors you may need to do three things:
1. install missing package
2. configure Oracle Middleware directories in etc/umc.cfg

In the worst case you need to prepare a new version of probe. It's described in separated part of the manual.

# First data collection
Now your UMC is ready to do data collection. Let's play with iostat.

Regular iostat returns nice looking, but not very useful for data collection output.

```
iostat 1 2
Linux 2.6.39-400.109.5.el6uek.x86_64 (soabpm-vm.site) 	02/28/2018 	_x86_64_	(4 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           0.56    0.89    0.23    0.02    0.00   98.30

Device:            tps   Blk_read/s   Blk_wrtn/s   Blk_read   Blk_wrtn
sda               1.14         3.81        18.03    1175630    5561450
sdc               0.67        14.78         8.97    4559104    2768814
sdb               1.56         4.53        21.31    1399084    6574529
dm-0              0.88         2.54        15.64     784530    4825160
dm-1              0.45         1.25         2.39     384168     736272

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           0.51    0.25    0.25    0.00    0.00   98.99

Device:            tps   Blk_read/s   Blk_wrtn/s   Blk_read   Blk_wrtn
sda               0.00         0.00         0.00          0          0
sdc               0.00         0.00         0.00          0          0
sdb               2.00         0.00        32.00          0         32
dm-0              0.00         0.00         0.00          0          0
dm-1              0.00         0.00         0.00          0          0

```

With UMC you get less nice response, but more ready for automated processing.

```bash
umc iostat collect 1 2

datetime,timezone,timestamp,system,source,Device,tps,kB_read/s,kB_wrtn/s,kB_read,kB_wrtn
2018-02-28 00:30:22,-0800,1519806622,soabpm-vm.site,iostat,sdb,1.56,2.27,10.65,699558,3288220
2018-02-28 00:30:22,-0800,1519806622,soabpm-vm.site,iostat,dm-0,0.88,1.27,7.82,392265,2412892
```

Notice change from Blk to kB, it's done by regular iostat parameter. Newer versions of iostat report performance using kB. 

## Log files
By default umc presents data as csv at stdout. It's by design as responsibility to write data to a log file was passsed to external utility. 

```bash
mkdir -p ~/obd/logs
umc ifconfig collect 1 60 | logdirector.pl -dir ~/obd/logs \
-name ifconfig -prefixDate -detectHeader -alwaysRotate \
-rotateByTime clock -timeLimit 10
ll ~/obd/logs
```

logdirector makes a lot of things related to saving csv stream to disk files. Above example will create files prefixed by date. Existing file will be rotated during start, and csv header will ba added to each new file. Rotation is done each 10 seconds using wall clock i.e. absolute time.

# On board diagnostics
The name of on bard diagnostics was stoled from car industry, where decades ago industry architects decided to equip each car with OBD-II interface making it possible to enable standardized diagnostic. On bard diagnostics is a natural extension of umc, converting csv-like collected data into other formats and other access means. The idea behind is to maintain proc-like directory and file structure enabling standardized way of storing and accessing system metrics. 


Basic directory structure looks like following:

```
obd
|-logs . . . . . . . . . umc logs are stored here
|-${resource}  . . . . . resource home directory
|  |-state . . . . . . . file with current state in map format (key=value)
|  |-dvdt  . . . . . . . directory with data rates [/s]
|  | \-state . . . . . . data rate state file in map format
|  |-header  . . . . . . file with list of metrics 
|  |-log . . . . . . . . directory with 20 recents measurements - csv
|  |-flags . . . . . . . directory with flags informing about special state
|  |-lock  . . . . . . . directory with locks for exclusive actions
|  \-tmp . . . . . . . . temporary files
(...)
```

above for network interfce:

```
obd
|-logs
|-eth0
|  |-state
|  \-dvdt
|  | \-state
|  |-header
|  |-log
|  |-flags
|  |-lock
|  \-tmp
(...)
```

## Maintain odb data
odb data is created on the fly, when requested, during each umc data collection. To do so pipe umc collector to csv2obd tool.

```
export status_root=$PWD/obd

umc ifconfig collect 1 5 eth0 | csv2obd --resource eth0
datetime,timezone,timestamp,system,source,device, RXpackets,RXerrors,RXdropped,RXoverruns,RXframe, TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier, collisions,txqueuelen, RXbytes,TXbytes
2020-02-13 13:05:47,+0000,1581599147,oci_box1,ifconfig,eth0,623333724,0,0,0,0,708979064,0,0,0,0,0,1000,354081818206,405490847158
2020-02-13 13:05:47,+0000,1581599148,oci_box1,ifconfig,eth0,623333808,0,0,0,0,708979168,0,0,0,0,0,1000,354081835282,405490880634
2020-02-13 13:05:49,+0000,1581599149,oci_box1,ifconfig,eth0,623333898,0,0,0,0,708979277,0,0,0,0,0,1000,354081852630,405490927640
2020-02-13 13:05:49,+0000,1581599150,oci_box1,ifconfig,eth0,623333992,0,0,0,0,708979403,0,0,0,0,0,1000,354081870466,405490976577
2020-02-13 13:05:51,+0000,1581599151,oci_box1,ifconfig,eth0,623334080,0,0,0,0,708979511,0,0,0,0,0,1000,354081887646,405491023533
```

After first run obd structure is created

```
tree obd
obd
└── eth0
    ├── header
    ├── log
    │   ├── header
    │   └── state
    ├── state
    └── tmp
        ├── header
        ├── line
        └── state.new

3 directories, 7 files
```

, with collected data. Notice the most important element - metrics presented in map format. It's a real time information - the file is created for each line displayed by umc for running sensor.

```
cat obd/eth0/state 
datetime=2020-02-1313:08:30
timezone=+0000
timestamp=1581599310
system=oci_box1
source=ifconfig
device=eth0
RXpackets=623348758
RXerrors=0
RXdropped=0
RXoverruns=0
RXframe=0
TXpackets=708997899
TXerrors=0
TXdropped=0
TXoverruns=0
TXcarrier=0
collisions=0
txqueuelen=1000
RXbytes=354084861814
TXbytes=405502291953
```

Other files are for further use. Header is stored to be able to create  headers in csv files, and most recent 20 measurement are stored in a form of sliding window file.

```
cat obd/eth0/header 
datetime,timezone,timestamp,system,source,device, RXpackets,RXerrors,RXdropped,RXoverruns,RXframe, TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier, collisions,txqueuelen, RXbytes,TXbytes

cat obd/eth0/log/state 
datetime,timezone,timestamp,system,source,device, RXpackets,RXerrors,RXdropped,RXoverruns,RXframe, TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier, collisions,txqueuelen, RXbytes,TXbytes
2020-02-13 13:08:26,+0000,1581599306,oci_box1,ifconfig,eth0,623348382,0,0,0,0,708997427,0,0,0,0,0,1000,354084791049,405502010513
2020-02-13 13:08:26,+0000,1581599307,oci_box1,ifconfig,eth0,623348495,0,0,0,0,708997567,0,0,0,0,0,1000,354084811140,405502151513
2020-02-13 13:08:28,+0000,1581599308,oci_box1,ifconfig,eth0,623348579,0,0,0,0,708997672,0,0,0,0,0,1000,354084827260,405502196919
2020-02-13 13:08:28,+0000,1581599309,oci_box1,ifconfig,eth0,623348675,0,0,0,0,708997795,0,0,0,0,0,1000,354084845624,405502246269
2020-02-13 13:08:30,+0000,1581599310,oci_box1,ifconfig,eth0,623348758,0,0,0,0,708997899,0,0,0,0,0,1000,354084861814,405502291953
```

## Data change rate
Some of sensors reports counters showing increment of metrics. Such counters are provided by e.g. network subsystem. It's in many cases information which is useless, as for this kind of devices we rather would like to see data rate. For such sensors you can apply dvdt filter.

```bash
umc ifconfig collect 1 5 eth0 | dvdt --resource eth0
datetime,timezone,timestamp,system,source,device,RXpackets,RXerrors,RXdropped,RXoverruns,RXframe,TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier,collisions,txqueuelen,RXbytes,TXbytes
2020-02-13 13:17:27,+0000,1581599848,oci_box1,ifconfig,eth0,39,0,0,0,0,52,0,0,0,0,0,0,7582,13780
2020-02-13 13:17:29,+0000,1581599849,oci_box1,ifconfig,eth0,70,0,0,0,0,74,0,0,0,0,0,0,13848,24248
2020-02-13 13:17:29,+0000,1581599850,oci_box1,ifconfig,eth0,73,0,0,0,0,79,0,0,0,0,0,0,14818,30134
2020-02-13 13:17:31,+0000,1581599851,oci_box1,ifconfig,eth0,102,0,0,0,0,120,0,0,0,0,0,0,19601,152884
```

This kind of filer is a special data modifier, storing it's data in dvdt directory.

```
obd
└── eth0
    ├── dvdt   . . . . directory with data rates [/s]
    │   └── state  . . file with current state in map format (key=value)
    ├── header
    ├── log
    │   ├── header
    │   └── state
    ├── state
    └── tmp
        ├── header
        ├── line
        └── state.new
```

Data rate dvdt state file keeps data in map format.

```
cat obd/eth0/dvdt/state 
datetime=2020-02-13 13:17:31
timezone=+0000
timestamp=1581599851
system=oci_box1
source=ifconfig
device=eth0
RXpackets=102
RXerrors=0
RXdropped=0
RXoverruns=0
RXframe=0
TXpackets=120
TXerrors=0
TXdropped=0
TXoverruns=0
TXcarrier=0
collisions=0
txqueuelen=0
RXbytes=19601
TXbytes=152884
```


## Getting data from obd
The purpose of maintaining obd information is ability to get current information about the system. Having sensor data in such format it's possible to get current value of e.x. RXbytes of eth0.

```
get eth0 RXbytes
354084861814
```

And now it comes to umc/obd coolness. It's possible to get metric modified by applied filter. 

```
get eth0 RXbytes dvdt
19601
```

## Chaining filters

Above two filters:first converting csv to map format, and second to compute data change rate, you may chain using pipe. Note that dvdt is used with data forwarding option, so you may decide if next filter should receive measured, or computed data. Below line forwards measured data, storing dvdt in obd/eth0/dvdt/state file. Note resource name set in variable to make command line shorter.

```
export resource=eth0; umc ifconfig collect 1 5 eth0 | csv2obd | dvdt --display forward

datetime,timezone,timestamp,system,source,device, RXpackets,RXerrors,RXdropped,RXoverruns,RXframe, TXpackets,TXerrors,TXdropped,TXoverruns,TXcarrier, collisions,txqueuelen, RXbytes,TXbytes
2020-02-13 13:24:19,+0000,1581600259,oci_box1,ifconfig,eth0,623432404,0,0,0,0,709099250,0,0,0,0,0,1000,354101904298,405551430235
2020-02-13 13:24:19,+0000,1581600260,oci_box1,ifconfig,eth0,623432497,0,0,0,0,709099365,0,0,0,0,0,1000,354101920712,405551488037
2020-02-13 13:24:21,+0000,1581600261,oci_box1,ifconfig,eth0,623432570,0,0,0,0,709099455,0,0,0,0,0,1000,354101934734,405551528481
2020-02-13 13:24:21,+0000,1581600262,oci_box1,ifconfig,eth0,623432670,0,0,0,0,709099581,0,0,0,0,0,1000,354101952730,405551642257
2020-02-13 13:24:23,+0000,1581600263,oci_box1,ifconfig,eth0,623432792,0,0,0,0,709099739,0,0,0,0,0,1000,354101976111,405551778809
```

Notice that as promised most recent csv line is stored as map in state file.

```
cat obd/eth0/state
datetime=2020-02-1313:24:23
timezone=+0000
timestamp=1581600263
system=oci_box1
source=ifconfig
device=eth0
RXpackets=623432792
RXerrors=0
RXdropped=0
RXoverruns=0
RXframe=0
TXpackets=709099739
TXerrors=0
TXdropped=0
TXoverruns=0
TXcarrier=0
collisions=0
txqueuelen=1000
RXbytes=354101976111
TXbytes=405551778809
```

, and dvdt state file:

```
cat obd/eth0/dvdt/state
datetime=2020-02-13 13:24:23
timezone=+0000
timestamp=1581600263
system=oci_box1
source=ifconfig
device=eth0
RXpackets=122
RXerrors=0
RXdropped=0
RXoverruns=0
RXframe=0
TXpackets=158
TXerrors=0
TXdropped=0
TXoverruns=0
TXcarrier=0
collisions=0
txqueuelen=0
RXbytes=23381
TXbytes=136552
```

## Flags
Flag makes it possible to mark some state of the resource. Most intuitive use to mark reaching thresholds, but it's just a marker with some name and timestmap, so may be used to anything.

To raise flag use, .... flag utility.

```
flag eth0 raise TX_over_threshold
```

To check if flag is set use the same utility. Flag check returns flag information using error code.

```
flag eth0 check TX_over_threshold; echo $?
1
```

You may raise flag several times. Check flag will inform about count of raises.

```
flag eth0 raise TX_over_threshold
flag eth0 raise TX_over_threshold
flag eth0 raise TX_over_threshold
flag eth0 check TX_over_threshold; echo $?
3
```

To clear the flag, use ... clear command.

```
flag eth0 clear TX_over_threshold
flag eth0 check TX_over_threshold; echo $?
0
```

As you see flag operation are per resource. 

# Conditional operations
Let's raise a flag when metric reached defined threshold...

```
when eth0/RXbytes gt 10000 flag raise TX_over_threshold
flag eth0 check TX_over_threshold; echo $?
1
```

, and clear it under other condition.

```
when eth0/RXbytes lt 8000 flag clear TX_over_threshold
flag eth0 check TX_over_threshold; echo $?
0
```

Let's run program when flag is raised

```
flag eth0 raise TX_over_threshold
when eth0 flag TX_over_threshold gt 0 run ls -l obd/eth0/flags
total 4
-rw-rw-r-- 1 opc opc 1 Feb 13 17:25 TX_over_threshold
```

, or when flag is cleared.

```
flag eth0 clear TX_over_threshold
when eth0 flag TX_over_threshold lt 1 run echo "All clear."
All clear.
```

Note that to avoid blocking by long running program e.g. tcpdump, the execution is passed to new process. To avoid starting more than one process for given resource lock file is maintained.

Let's simulate long running program with sleep.

```
cat >runlong <<EOF
#!/bin/bash

echo Runloooooooong started with parameters: \$@
sleep 30
echo Runloooooooong done.
EOF
chmod +x runlong
```

```
flag eth0 raise TX_over_threshold
when eth0 flag TX_over_threshold gt 0 run with context ./runlong
Runloooooooong started with parameters: 17248 eth0 TX_over_threshold 3 0
```

when you will start the same before previous program finishes, umc will block process start.

```
when eth0 flag TX_over_threshold gt 0 run with context ./runlong
Warning: runlong for attribute TX_over_threshold at eth0 is being executed. Info: cmd=runlong,attribute=TX_over_threshold,id=17248,pid=1200
```

File lock is stored in obd/eth0/lock directory. Process identification is performed by attribute, PID, and random number applied to starting process with "with context" clause. Note that process takes arguments of: $seed, $resource, $flag, $value, $threshold. Prepare process wrapper to accommodate.

You may start process without passing context, such technique may be used for programs exclusively running for the resource.


```
when eth0 flag TX_over_threshold gt 0 run ./runlong Hey
[opc@oci_box1 rstyczynski]$ Runloooooooong started with parameters: Hey

when eth0 flag TX_over_threshold gt 0 run ./runlong Hey
Warning: runlong for attribute . at eth0 is being executed. Info: cmd=runlong,attribute=.,id=.,pid=3779,
```

, and

```
run eth0 ./runlong Hey
Runloooooooong started with parameters: Hey

run eth0 ./runlong Hey
Warning: runlong for attribute . at eth0 is being executed. Info: cmd=runlong,attribute=.,id=.,pid=3848,
```

## Trigger condition after each measurement
Condition check is a synchronous operation triggered by some action. Above all checks were triggered manually from command line. umc provides foreach tool which delivers ability to run checks when new measurement arrives.



```
umc ifconfig collect 1 60 eth0 | csv2obd | dvdt | foreach line silently when eth0/dvdt/RXbytes gt 50000 print

eth0/dvdt 2020-02-13 18:08:57,+0000,1581617337,oci_box1,ifconfig,eth0,632,0,0,0,0,339,0,0,0,0,0,0,3739172,111574 RXbytes 401279 50000
eth0/dvdt 2020-02-13 18:08:57,+0000,1581617338,oci_box1,ifconfig,eth0,299,0,0,0,0,174,0,0,0,0,0,0,1638418,57656 RXbytes 3739172 50000
eth0/dvdt 2020-02-13 18:08:59,+0000,1581617339,oci_box1,ifconfig,eth0,310,0,0,0,0,175,0,0,0,0,0,0,1834236,133274 RXbytes 1638418 50000
eth0/dvdt 2020-02-13 18:09:00,+0000,1581617340,oci_box1,ifconfig,eth0,325,0,0,0,0,189,0,0,0,0,0,0,1869094,156622 RXbytes 1834236 50000
```

Above line triggered echo on eth0 read bytes rate bigger then threshold. umc performs condition check for each received line from data collector/filters.

Note that foreach uses a trick similar to xargs. In fact piped csv data is ignored, and after each line 'when' command goes to obd/eth0/dvdt/state file to get value of RXbytes and copare with given threshold. The trick works as 'dvdt' filter before, updates state file for each received line. Note 'silently' clause which blocks regular csv data display. Such mode is rather used for debug, as normally filters should pass csv trough.

Let's set flag each time the threshold is passed. 

```
umc ifconfig collect 1 15 eth0 | csv2obd | dvdt | foreach line silently when eth0/RXbytes dvdt gt 50000 flag raise RX_over_threshold

flag eth0 check RX_over_threshold; echo $?
5
```

Above shows that during 15 seconds of collecting data, data read on eth0 was faster than 50000 bytes/s 5 times, however it's not required that all 5 times created one stream of bursted data. Flag raised 5 times, just means that durign measurement 5 times threshold was reached.

## More complex examples

### Chaining real time conditional execution with real time conditional flag raise and clear.

During presented below oepration netowrk card received twice higer load. First time for 10+8 seconds, and second time for 10+3 seconds.

```
# clear flag
flag eth0 clear RX_over_threshold

umc ifconfig collect 1 60 eth0 | 
csv2obd | dvdt | 
foreach line when eth0/RXbytes dvdt gt 50000 flag raise RX_over_threshold | 
foreach line when eth0/RXbytes dvdt lt 25000 flag clear RX_over_threshold | 
foreach line silently when eth0 flag RX_over_threshold gt 10 run echo


2020-02-13 19:31:53,+0000,1581622313,oci_box1-wls-1,ifconfig,eth0,322,0,0,0,0,189,0,0,0,0,0,0,1869257,107270
2020-02-13 19:31:53,+0000,1581622314,oci_box1-wls-1,ifconfig,eth0,320,0,0,0,0,180,0,0,0,0,0,0,1870002,57044
2020-02-13 19:31:55,+0000,1581622315,oci_box1-wls-1,ifconfig,eth0,321,0,0,0,0,199,0,0,0,0,0,0,1837701,60406
2020-02-13 19:31:55,+0000,1581622316,oci_box1-wls-1,ifconfig,eth0,314,0,0,0,0,193,0,0,0,0,0,0,1802464,152218
2020-02-13 19:31:57,+0000,1581622317,oci_box1-wls-1,ifconfig,eth0,319,0,0,0,0,186,0,0,0,0,0,0,1933452,57820
2020-02-13 19:31:57,+0000,1581622318,oci_box1-wls-1,ifconfig,eth0,338,0,0,0,0,220,0,0,0,0,0,0,1805836,148180
2020-02-13 19:32:00,+0000,1581622320,oci_box1-wls-1,ifconfig,eth0,88,0,0,0,0,110,0,0,0,0,0,0,17424,49952
2020-02-13 19:32:00,+0000,1581622321,oci_box1-wls-1,ifconfig,eth0,96,0,0,0,0,121,0,0,0,0,0,0,17636,146530


2020-02-13 19:32:26,+0000,1581622346,oci_box1-wls-1,ifconfig,eth0,319,0,0,0,0,193,0,0,0,0,0,0,1836562,58526
2020-02-13 19:32:26,+0000,1581622347,oci_box1-wls-1,ifconfig,eth0,317,0,0,0,0,178,0,0,0,0,0,0,1868114,56472
2020-02-13 19:32:28,+0000,1581622348,oci_box1-wls-1,ifconfig,eth0,311,0,0,0,0,195,0,0,0,0,0,0,1801902,151510
```

### Collect, log, compute rate, and log rate

Logdirector is extended no with option -tee what makes it possible to use logger as an in pipe element. 

```
log_root=~/log; mkdir -p $log_root

export resource= eth0
umc ifconfig collect 1 5 eth0 |
csv2obd |
logdirector.pl -dir $log_root -name ifconfig_ eth0 -detectHeader -tee |
dvdt |
logdirector.pl -dir $log_root -name ifconfig_eth0_dvdt -detectHeader

ll $log_root

```


# Oracle Middleware
UMC collects data from: WebLogic, OSB, and SOA composite. WebLogic data is collected trough regular mBeans, OSB via wlst, and SOA uses DMS subsystem available in WebLogic. 


## Configuration
To configure UMC for Oracle Middleware, edit etc/umc.cfg to provide required information about home and domain directories. Note that providing WebLogic domain directory is important, as UMC probes are started from domain directory to bypass a need of authentication. 

```
vi umc/etc/umc.cfg

#---------------------------------------------------------------------------------------
#--- platform location & specific configuration
#---------------------------------------------------------------------------------------

#TODO configure below variables to used Oracle SOA data collectors
export FMW_HOME=/oracle/fmwhome
export SOA_HOME=$FMW_HOME/Oracle_SOA1
export OSB_HOME=$FMW_HOME/Oracle_OSB1
export WLS_HOME=$FMW_HOME/wlserver_10.3/server
export DOMAIN_HOME=$FMW_HOME/user_projects/domains/dev_soasuite

#---------------------------------------------------------------------------------------
#--- reporting
#---------------------------------------------------------------------------------------

export CSVdelimiter=,
```

## WebLogic ##
WebLogic metrics are collected in several areas: socket, requests, threads, channel, jmsruntime, jmsserver, and datasource. Use --subsytem option to set which part should be harvested. By default it takes general set of data.


Default set of data:

```
umc wls collect 1 2

datetime,timezone,timestamp,system,source,domain,serverName,subsystem,sockets_open,sockets_opened,heap_size,heap_size_max,heap_free,heap_free_pct,jvm_uptime,thread_total,thread_idle,thread_hogging,thread_standby,request_queue,request_pending,request_completed,request_troughput
2018-03-08 00:14:33,-0800,1520496873,soabpm-vm.site,wls,dev_soasuite,UCM_server1,general,3,3,536870912,n/a,106960216,19,n/a,6,1,0,4,0,0,38792,1.4992503748125936
2018-03-08 00:14:33,-0800,1520496873,soabpm-vm.site,wls,dev_soasuite,AdminServer,general,8,8,2147483648,n/a,308482224,14,n/a,27,20,0,5,0,0,1188447,10.494752623688155
2018-03-08 00:14:33,-0800,1520496874,soabpm-vm.site,wls,dev_soasuite,UCM_server1,general,3,3,536870912,n/a,106960216,19,n/a,6,1,0,4,0,0,38792,1.4992503748125936
2018-03-08 00:14:33,-0800,1520496874,soabpm-vm.site,wls,dev_soasuite,AdminServer,general,8,8,2147483648,n/a,308482224,14,n/a,27,20,0,5,0,0,1188447,10.494752623688155
```


Data collected from channel:

```
umc wls collect 1 2 --subsystem=channel

datetime,timezone,timestamp,system,source,domain,serverName,subsystem,channelName,accepts,bytesReceived,byteSent,connections,msgReceived,msgSent
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,iiop,Default[iiop],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,http,Default[http],169,446329,22815,0,169,169
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,t3,Default[t3],1,12497514,13909908,1,8196,8196
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,ldap,Default[ldap],1,13835852,0,1,6745,0
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,iiop,Default[iiop],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,http,Default[http],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,t3,Default[t3],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496153,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,ldap,Default[ldap],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,iiop,Default[iiop],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,http,Default[http],169,446329,22815,0,169,169
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,t3,Default[t3],1,12497514,13909908,1,8196,8196
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,UCM_server1,channel,ldap,Default[ldap],1,13835852,0,1,6745,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,iiop,Default[iiop],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,http,Default[http],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,t3,Default[t3],0,0,0,0,0,0
2018-03-08 00:02:33,-0800,1520496154,soabpm-vm.site,wls,dev_soasuite,AdminServer,channel,ldap,Default[ldap],0,0,0,0,0,0
```

JMS runtime:

```bash
umc wls collect 1 2 --subsystem=jmsruntime

datetime,timezone,timestamp,system,source,domain,serverName,subsystem,runtimeName,connections,connectionsHigh,connectionsTotal,servers,serversHigh,serversTotal
2018-03-08 00:16:09,-0800,1520496969,soabpm-vm.site,wls,dev_soasuite,UCM_server1,jmsruntime,UCM_server1.jms,0,0,0,0,0,0
2018-03-08 00:16:09,-0800,1520496969,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsruntime,AdminServer.jms,44,44,27668,9,9,9
2018-03-08 00:16:09,-0800,1520496970,soabpm-vm.site,wls,dev_soasuite,UCM_server1,jmsruntime,UCM_server1.jms,0,0,0,0,0,0
2018-03-08 00:16:09,-0800,1520496970,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsruntime,AdminServer.jms,44,44,27668,9,9,9
```

JMS Servers:

```
umc wls collect 1 2 --subsystem=jmsserver

datetime,timezone,timestamp,system,source,domain,serverName,subsystem,jmsServerName,bytes,bytesHigh,bytesPageable,bytesPagedIn,bytesPagedOut,bytesPending,bytesReceived,bytesThresholdTime,destinations,destinationsHigh,destinationsTotal,messages,messagesHigh,messagesPageable,messagesPagedIn,messagesPagedOut,messagesPending,messagesReceived,messagesThresholdTime,pending,transactions,sessionPoolsCurrent,sessionPoolsHigh,sessionPoolsTotal
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,WseeJmsServer,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,BPMJMSServer,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,SOAJMSServer,1529,1529,1529,0,0,0,0,0,10,10,10,3,3,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,AGJMSServer,0,61,0,0,0,0,28072,0,2,2,2,0,1,0,0,0,0,462,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,PS6SOAJMSServer,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,JRFWSAsyncJmsServer,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,UMSJMSServer,0,0,0,0,0,0,0,0,6,6,6,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497011,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,wlsbJMSServer,0,0,0,0,0,0,0,0,8,8,8,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,WseeJmsServer,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,BPMJMSServer,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,SOAJMSServer,1529,1529,1529,0,0,0,0,0,10,10,10,3,3,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,AGJMSServer,0,61,0,0,0,0,28072,0,2,2,2,0,1,0,0,0,0,462,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,PS6SOAJMSServer,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,JRFWSAsyncJmsServer,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,UMSJMSServer,0,0,0,0,0,0,0,0,6,6,6,0,0,0,0,0,0,0,0,None,None,0,0,0
2018-03-08 00:16:51,-0800,1520497012,soabpm-vm.site,wls,dev_soasuite,AdminServer,jmsserver,wlsbJMSServer,0,0,0,0,0,0,0,0,8,8,8,0,0,0,0,0,0,0,0,None,None,0,0,0
```

Data sources:

```
umc wls collect 1 2 --subsystem=datasource

datetime,timezone,timestamp,system,source,domain,serverName,subsystem,dsName,capacity,capacityHigh,numAvailable,numUnavailable,highestNumAvailable,highestNumUnavailable,activeConnectionsAverage,activeConnectionsCurrent,activeConnectionsHigh,connectionsTotal,connectionDelayTime,leakedConnections,reserveRequest,failedReserveRequest,failuresToReconnect,waitingForConnectionCurrent,waitingForConnectionFailureTotal,waitingForConnectionHigh,waitingForConnectionSuccessTotal,waitingForConnectionTotal,waitSecondsHigh,prepStmtCacheAccess,prepStmtCacheAdd,prepStmtCacheCurrentSize,prepStmtCacheDelete,prepStmtCacheHit,prepStmtCacheMiss
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,UCM_server1,datasource,CSDS,2,3,2,0,3,3,0,0,3,16,102,0,695,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,quoteDS,1,1,1,0,1,1,0,0,1,1,22,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,jndi/test,1,1,1,0,1,1,0,0,1,1,454,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,EDNDataSource,1,2,0,1,1,2,1,1,2,2,48,0,11113,0,0,0,0,0,0,0,0,11112,1,1,0,11111,1
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,wlsbjmsrpDataSource,5,5,5,0,5,1,0,0,1,5,22,0,3,0,0,0,0,0,0,0,0,9,3,3,0,6,3
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-owsm,1,1,1,0,1,1,0,0,1,63,18,0,3545,0,0,0,0,0,0,0,0,2,1,1,0,1,1
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-soa,1,2,1,0,2,2,0,0,2,63,19,0,5301,0,0,0,0,0,0,0,0,6,1,1,0,5,1
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,OraSDPMDataSource,1,1,1,0,1,1,0,0,1,63,19,0,938,0,0,0,0,0,0,0,0,2,1,1,0,1,1
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-SpacesDS,10,10,10,0,10,1,0,0,1,10,21,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,EDNLocalTxDataSource,2,3,0,2,2,3,2,2,3,3,50,0,22230,0,0,0,0,0,0,0,0,22231,5,5,0,22226,5
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,SOALocalTxDataSource,1,2,1,0,2,2,0,0,2,63,19,0,3129,0,0,0,0,0,0,0,0,3,2,2,0,1,2
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,SOADataSource,1,2,1,0,2,2,0,0,2,63,21,0,109315,0,0,0,0,0,0,0,0,2818,56,10,46,2762,56
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,soademoDatabase,1,1,1,0,1,1,0,0,1,1,22,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497228,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,ps6workshop,1,1,1,0,1,1,0,0,1,1,24,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,UCM_server1,datasource,CSDS,2,3,2,0,3,3,0,0,3,16,102,0,695,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,quoteDS,1,1,1,0,1,1,0,0,1,1,22,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,jndi/test,1,1,1,0,1,1,0,0,1,1,454,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,EDNDataSource,1,2,0,1,1,2,1,1,2,2,48,0,11113,0,0,0,0,0,0,0,0,11112,1,1,0,11111,1
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,wlsbjmsrpDataSource,5,5,5,0,5,1,0,0,1,5,22,0,3,0,0,0,0,0,0,0,0,9,3,3,0,6,3
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-owsm,1,1,1,0,1,1,0,0,1,63,18,0,3545,0,0,0,0,0,0,0,0,2,1,1,0,1,1
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-soa,1,2,1,0,2,2,0,0,2,63,19,0,5301,0,0,0,0,0,0,0,0,6,1,1,0,5,1
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,OraSDPMDataSource,1,1,1,0,1,1,0,0,1,63,19,0,938,0,0,0,0,0,0,0,0,2,1,1,0,1,1
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,mds-SpacesDS,10,10,10,0,10,1,0,0,1,10,21,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,EDNLocalTxDataSource,2,3,0,2,2,3,2,2,3,3,50,0,22230,0,0,0,0,0,0,0,0,22231,5,5,0,22226,5
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,SOALocalTxDataSource,1,2,1,0,2,2,0,0,2,63,19,0,3129,0,0,0,0,0,0,0,0,3,2,2,0,1,2
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,SOADataSource,1,2,1,0,2,2,0,0,2,63,21,0,109315,0,0,0,0,0,0,0,0,2818,56,10,46,2762,56
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,soademoDatabase,1,1,1,0,1,1,0,0,1,1,22,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2018-03-08 00:20:28,-0800,1520497229,soabpm-vm.site,wls,dev_soasuite,AdminServer,datasource,ps6workshop,1,1,1,0,1,1,0,0,1,1,24,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
```

## OSB ##
OSB provides multiple metrics, and UMC harvest subset of them related to: (a) Proxy service, (b) Business service, and (c) URI. 

Note that before collecting data you need to enable monitoring (sbconsole->service->operational settings->monitoring). Once enabled, UMC is able to harvest performance counters.

Data collection from Proxy service:

```
umc businessservice collect 1 2 --metrics_type=SERVICE

datetime,timezone,timestamp,system,source,service_type,path,name,metrics_type,error-count_count,failover-count_count,failure-rate_count,message-count_count,response-time_average,response-time_max,response-time_min,response-time_sum,severity-all_count,sla-severity-all_count,sla-severity-critical_count,sla-severity-fatal_count,sla-severity-major_count,sla-severity-minor_count,sla-severity-normal_count,sla-severity-warning_count,success-rate_count,throttling-time_average,throttling-time_max,throttling-time_min,throttling-time_sum,uri-offline-count_current,uri-offline-count_initial,wss-error_count
2018-02-28 04:46:32,-0800,1519821992,soabpm-vm.site,businessservice,SERVICE,TEST2,TriggerSOA,BusinessService,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,100,0,0,0,0.0,0,0,0
2018-02-28 04:46:32,-0800,1519821992,soabpm-vm.site,businessservice,SERVICE,TEST1,TestService1,BusinessService,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,100,0,0,0,0.0,0,0,0
2018-02-28 04:46:32,-0800,1519821993,soabpm-vm.site,businessservice,SERVICE,TEST2,TriggerSOA,BusinessService,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,100,0,0,0,0.0,0,0,0
2018-02-28 04:46:32,-0800,1519821993,soabpm-vm.site,businessservice,SERVICE,TEST1,TestService1,BusinessService,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,100,0,0,0,0.0,0,0,0
```

Data collection from Business service:

```
umc businessservice collect 1 2 --metrics_type=OPERATION

datetime,timezone,timestamp,system,source,service_type,path,name,metrics_type,elapsed-time#average,elapsed-time#max,elapsed-time#min,elapsed-time#sum,error-count#count,message-count#count
2018-02-28 04:48:27,-0800,1519822107,soabpm-vm.site,businessservice,WEBSERVICE_OPERATION,TEST2,TriggerSOA,BusinessService,0,0,0,0.0,0,0
2018-02-28 04:48:27,-0800,1519822107,soabpm-vm.site,businessservice,WEBSERVICE_OPERATION,TEST1,TestService1,BusinessService,0,0,0,0.0,0,0
2018-02-28 04:48:27,-0800,1519822108,soabpm-vm.site,businessservice,WEBSERVICE_OPERATION,TEST2,TriggerSOA,BusinessService,0,0,0,0.0,0,0
2018-02-28 04:48:27,-0800,1519822108,soabpm-vm.site,businessservice,WEBSERVICE_OPERATION,TEST1,TestService1,BusinessService,0,0,0,0.0,0,0
```

Data collection from URI:

```
umc businessservice collect 1 2 --metrics_type=URI

datetime,timezone,timestamp,system,source,service_type,path,name,metrics_type,error-count#count,message-count#count,response-time#average,response-time#max,response-time#min,response-time#sum,status#current,status#initial
2018-02-28 04:49:05,-0800,1519822145,soabpm-vm.site,businessservice,URI,TEST2,TriggerSOA,BusinessService,0,0,0,0,0,0.0,1,1
2018-02-28 04:49:05,-0800,1519822145,soabpm-vm.site,businessservice,URI,TEST1,TestService1,BusinessService,0,0,0,0,0,0.0,1,1
2018-02-28 04:49:05,-0800,1519822146,soabpm-vm.site,businessservice,URI,TEST2,TriggerSOA,BusinessService,0,0,0,0,0,0.0,1,1
2018-02-28 04:49:05,-0800,1519822146,soabpm-vm.site,businessservice,URI,TEST1,TestService1,BusinessService,0,0,0,0,0,0.0,1,1
```

## Composite ##
SOA provides massive information about internal systems. Out of all possibilities, UMC provides access to composite information, stored in DMS subsystem at 'oracle_soainfra:soainfra_binding_rollup_domain'. DMS data collection is enabled by default.

```
umc soabindings collect 1 2

datetime,timezone,timestamp,system,source,ServerName, soainfra_composite,soainfra_composite_assembly_member,soainfra_composite_assembly_member_type,soainfra_composite_revision,soainfra_domain, Messages.averageTime,Messages.completed,Messages.throughput,Messages.time,Messages.totalTime, MessagesEvents.count,MessagesEvents.throughput,Messages.count, error.rate,Errors.count,Errors.throughput
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,SalesQuoteProcess,SaveQuote,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,AddDiscount.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,UpgradeCustomer.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,StartEURentCaseService_ep,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,EURent.directBindingService,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,GetCar.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,GetCustomerStatus.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,EURent.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,ChargeCustomer.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,DropOff.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,validationForCC,getStatusByCC,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,validationForCC,getCreditValidation,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,receivePO,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,WriteApprovalResults,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_UPS,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_USPS,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_FedEx,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,getCreditCardStatus,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,DBTest,Service1,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823118,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,DBTest,testdb,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,SalesQuoteProcess,SaveQuote,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,AddDiscount.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,UpgradeCustomer.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,StartEURentCaseService_ep,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,EURent.directBindingService,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,GetCar.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,GetCustomerStatus.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,EURent.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,ChargeCustomer.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,EURent,DropOff.service,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,validationForCC,getStatusByCC,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,validationForCC,getCreditValidation,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,receivePO,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,WriteApprovalResults,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_UPS,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_USPS,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,JMS_FedEx,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,POProcessing,getCreditCardStatus,REFERENCEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,DBTest,Service1,SERVICEs,1.0,default
2018-02-28 05:05:18,-0800,1519823119,soabpm-vm.site,soabindings,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0,AdminServer,DBTest,testdb,REFERENCEs,1.0,default

```

# Bulk data collection #
In real sutiation e.g. during performace tests it's needed to start collections of multiple (if not all) pieces of information. UMC is equipped with utility to support start of multiple probes at the same time.

Bulk utility additionally uses log splitter, which splits log files every 15 minutes (clock time) and saves in directory with current date. 

To start 10 collections with 1 second interval use the following command:

```
umc_collectAll.sh 1 10 "vmstat free top uptime meminfo tcpext netstattcp ifconfig iostat pingSocket" 

Note: Oracle SOA not configured. Update etc/umc.cfg to be able to use SOA related components of the package.
Universal Metrics Collector initialized.

Batch UMC collector initializes data collection for following probes:
-> vmstat
-> free
-> top
-> uptime
-> meminfo
-> tcpext
-> netstattcp
-> ifconfig
-> iostat
-> pingSocket

Starting umc vmstat collect 10 1 ...
Starting umc free collect 10 1 ...
Starting umc top collect 10 1 ...
Starting umc uptime collect 10 1 ...
Starting umc meminfo collect 10 1 ...
Starting umc tcpext collect 10 1 ...
Starting umc netstattcp collect 10 1 ...
Starting umc ifconfig collect 10 1 ...
Starting umc iostat collect 10 1 ...
Starting umc pingSocket collect 10 1 ...

Waiting for probes to finish data collection.
10,9,8,7,6,5,4,3,2,1,done.
```

Note that following error may be reported, which may be ignored:

```
close failed in file object destructor:
sys.excepthook is missing
lost sys.stderr
```

Data files are written in directory named with current date. 

```
[vagrant@oracle ~]$ ls -l 2018-03-22
total 40
-rw-r----- 1 vagrant vagrant  276 Mar 22 08:00 2018-03-22-080036_free.log
-rw-r----- 1 vagrant vagrant  413 Mar 22 08:00 2018-03-22-080036_ifconfig.log
-rw-r----- 1 vagrant vagrant 1053 Mar 22 08:00 2018-03-22-080036_iostat.log
-rw-r----- 1 vagrant vagrant  772 Mar 22 08:00 2018-03-22-080036_meminfo.log
-rw-r----- 1 vagrant vagrant  366 Mar 22 08:00 2018-03-22-080036_netstattcp.log
-rw-r----- 1 vagrant vagrant  998 Mar 22 08:00 2018-03-22-080036_pingSocket_general.log
-rw-r----- 1 vagrant vagrant 1478 Mar 22 08:00 2018-03-22-080036_tcpext.log
-rw-r----- 1 vagrant vagrant 1451 Mar 22 08:00 2018-03-22-080036_top.log
-rw-r----- 1 vagrant vagrant  158 Mar 22 08:00 2018-03-22-080036_uptime.log
-rw-r----- 1 vagrant vagrant  369 Mar 22 08:00 2018-03-22-080036_vmstat.log
```

## Special use ##
To specify probes parameters use colon instead of spaces. To write data to another directory, use --logDir argument. To store files in a subdirectory - possibly to given test identifier, use --testId argument. Finally to run data collection in background use --nonblocking flag. 

```
umc_collectAll.sh 1 10 "iostat vmstat free uptime ifconfig:eth0" --logDir=/home/vagrant/perfdata --testId=A --nonblocking

Note: Oracle SOA not configured. Update etc/umc.cfg to be able to use SOA related components of the package.
Universal Metrics Collector initialized.

Batch UMC collector initializes data collection for following probes:
-> iostat
-> vmstat
-> free
-> uptime
-> ifconfig eth0

Starting umc iostat collect 10 1 ...
Starting umc vmstat collect 10 1 ...
Starting umc free collect 10 1 ...
Starting umc uptime collect 10 1 ...
Starting umc ifconfig collect 10 1 eth0 ...

Probes left running in background. Use umc_stopAll.sh to stop.
```

Process runs in background, writing files to date directory under /home/vagrant/perfdata/A.

```
[vagrant@oracle ~]$ ls -l /home/vagrant/perfdata/A
total 4
drwxr-x--- 2 vagrant vagrant 4096 Mar 22 08:34 2018-03-22

[vagrant@oracle ~]$ ls -l /home/vagrant/perfdata/A/2018-03-22/
total 20
-rw-r----- 1 vagrant vagrant  276 Mar 22 08:34 2018-03-22-083456_free.log
-rw-r----- 1 vagrant vagrant  314 Mar 22 08:35 2018-03-22-083456_ifconfig.log
-rw-r----- 1 vagrant vagrant 1027 Mar 22 08:35 2018-03-22-083456_iostat.log
-rw-r----- 1 vagrant vagrant  158 Mar 22 08:35 2018-03-22-083456_uptime.log
-rw-r----- 1 vagrant vagrant  366 Mar 22 08:35 2018-03-22-083456_vmstat.log
```

To stop background data collection use umc_stopAll.sh

```
umc_collectAll.sh 1 10 "iostat vmstat free uptime ifconfig:eth0" --logDir=/home/vagrant/perfdata --testId=A --nonblocking

Note: Oracle SOA not configured. Update etc/umc.cfg to be able to use SOA related components of the package.
Universal Metrics Collector initialized.

Batch UMC collector initializes data collection for following probes:
-> iostat
-> vmstat
-> free
-> uptime
-> ifconfig eth0

Starting umc iostat collect 10 1 ...
Starting umc vmstat collect 10 1 ...
Starting umc free collect 10 1 ...
Starting umc uptime collect 10 1 ...
Starting umc ifconfig collect 10 1 eth0 ...

Probes left running in background. Use umc_stopAll.sh to stop.


[vagrant@oracle ~]$ umc_stopAll.sh
Active processes:
vagrant  11474  0.0  0.1  64036   836 pts/0    S    08:38   0:00 /bin/bash /home/vagrant/umc/bin/umc_collectAll.sh 1 10 iostat vmstat free uptime ifconfig:eth0 --logDir=/home/vagrant/perfdata --testId=A --nonblocking
vagrant  11511  0.0  0.1  64036   836 pts/0    S    08:38   0:00 /bin/bash /home/vagrant/umc/bin/umc_collectAll.sh 1 10 iostat vmstat free uptime ifconfig:eth0 --logDir=/home/vagrant/perfdata --testId=A --nonblocking
vagrant  11586  0.0  0.1  64036   836 pts/0    S    08:38   0:00 /bin/bash /home/vagrant/umc/bin/umc_collectAll.sh 1 10 iostat vmstat free uptime ifconfig:eth0 --logDir=/home/vagrant/perfdata --testId=A --nonblocking
vagrant  11627  0.0  0.1  64036   828 pts/0    S    08:38   0:00 /bin/bash /home/vagrant/umc/bin/umc_collectAll.sh 1 10 iostat vmstat free uptime ifconfig:eth0 --logDir=/home/vagrant/perfdata --testId=A --nonblocking

Stopped umc process 11474 and all child processes.
Stopped umc process 11511 and all child processes.
Stopped umc process 11586 and all child processes.
Stopped umc process 11627 and all child processes.
All clean.
```


# When the utility is not available
When the utility is missing umc will report the problem.

```
sudo yum remove sysstat

umc iostat collect 1 2
Error! Reason: utility not recognized as supported tool.
Available versions:
--- /home/oracle/ttMetrics/tools/Linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/Linux/systat/10.0.3/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/10.0.3/iostat
Your version:
--- systat/
```

The same will be reported by umc test.

```
umc test

vmstat:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with vmstat ...OK
free:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with free ...OK
top:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with top ...OK
uptime:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with uptime ...OK
meminfo:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with meminfo ...OK
tcpext:Testing compatibility of /home/oracle/ttMetrics/tools/linux/procps/3.2.8 with tcpext ...OK
netstattcp:Testing compatibility of /home/oracle/ttMetrics/tools/linux/net-tools/1.60 with netstattcp ...OK
ifconfig:Testing compatibility of /home/oracle/ttMetrics/tools/linux/net-tools/1.60 with ifconfig ...OK
iostat:Error! Reason: utility not recognized as supported tool.
Available versions:
--- /home/oracle/ttMetrics/tools/Linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/Linux/systat/10.0.3/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/10.0.3/iostat
Your version:
--- systat/
Testing compatibility of with iostat ...Error! Reason: The tool not found in given directory.
Error
Error! Reason: utility not recognized as supported tool.
Available versions:
--- /home/oracle/ttMetrics/tools/Linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/Linux/systat/10.0.3/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/9.0.4/iostat
--- /home/oracle/ttMetrics/tools/linux/systat/10.0.3/iostat
Your version:
--- systat/
soabindings:Testing compatibility of /home/oracle/ttMetrics/tools/linux/java/wls/soa/11/1/1/7.0 with soabindings ...OK
businessservice:Testing compatibility of /home/oracle/ttMetrics/tools/linux/java/wls/soa/11/1/1/7.0 with businessservice ...OK
```

Just add missing package, and reinitialize UMC.

```
sudo yum install sysstat
. umc/bin/umc.h 

Universal Metrics Collector initialized.
```

Now you can use iostat probe.

```
umc iostat collect 1 2

datetime,timezone,timestamp,system,source,Device,tps,kB_read/s,kB_wrtn/s,kB_read,kB_wrtn
2018-02-28 02:42:51,-0800,1519814571,soabpm-vm.site,iostat,sdb,1.56,2.42,10.63,765586,3366132
2018-02-28 02:42:51,-0800,1519814571,soabpm-vm.site,iostat,dm-0,0.98,2.61,10.56,826393,3342164
2018-02-28 02:42:51,-0800,1519814571,soabpm-vm.site,iostat,dm-1,0.53,0.61,1.50,192980,474292
2018-02-28 02:42:51,-0800,1519814572,soabpm-vm.site,iostat,sda,0.00,0.00,0.00,0,0
2018-02-28 02:42:51,-0800,1519814572,soabpm-vm.site,iostat,sdc,0.00,0.00,0.00,0,0
2018-02-28 02:42:51,-0800,1519814572,soabpm-vm.site,iostat,sdb,2.00,0.00,16.00,0,16
2018-02-28 02:42:51,-0800,1519814572,soabpm-vm.site,iostat,dm-0,0.00,0.00,0.00,0,0
2018-02-28 02:42:51,-0800,1519814572,soabpm-vm.site,iostat,dm-1,0.00,0.00,0.00,0,0
2018-02-28 02:42:53,-0800,1519814573,soabpm-vm.site,iostat,sda,4.00,0.00,44.00,0,44
2018-02-28 02:42:53,-0800,1519814573,soabpm-vm.site,iostat,sdc,0.00,0.00,0.00,0,0
2018-02-28 02:42:53,-0800,1519814573,soabpm-vm.site,iostat,sdb,0.00,0.00,0.00,0,0
2018-02-28 02:42:53,-0800,1519814573,soabpm-vm.site,iostat,dm-0,11.00,0.00,44.00,0,44
2018-02-28 02:42:53,-0800,1519814573,soabpm-vm.site,iostat,dm-1,0.00,0.00,0.00,0,0
```

# Required packages
UMC is based mainly on bash, however requires set of packages to work properly. Python 2.7 and perl are used by utility scripts supporting UMC in some aspects as reading yaml configuration, or prefixing stream with timestamps.

Install packages for Ubuntu:

```bash
apt-get clean
apt-get update
apt-get install -y curl
apt-get install -y python python-yaml
apt-get install -y perl
apt-get install -y locales
apt-get install -y sysstat
apt-get install -y net-tools
locale-gen en_US.UTF-8
```

For Redhat:

```bash
sudo yum install -y git curl python \
python-yaml perl locales sysstat net-tools

```

If it's not possible to install python 2.7 due to lack of priviliges, you may install it in your home directory. Details at this blog: http://thelazylog.com/install-python-as-local-user-on-linux/


# Extend probe definition
TODO


# TODO Tools
1. Ping
2. Add node column to identify process e.g. WebLogic instance on a host
3. Add long timestamp (raw long value of Linux time) as a generic column
4. Add version information: os, utils
5. switch iostat into extended mode

# TODO General
1. Automatically execute test for given OS with '0' level utilities. Once executed stores information in directory that test was passed or failed. Invoke should use this information.
2. Invoke performs header test upon first run to write result to files. During next runs it's verified if test was passed or not.
3. Add "procps version" e.g. free -V to validate compatibility of tools and scripts
4. Recognize data formatting returned by OS tools. Is decimal delimiter a dot or comma?
5. Add data description to fields: scale min, max, logarithmic, delta, data label as e.g. kB, MB/s
6. Add data correlation information
7. Add data hierarchy information to fields e.g. ProcessRunQueue -> cpu.ProcessRunQueue

# Open issues
1. Are extra columns allowed in CSV file?

# Author
rstyczynski@gmail.com, https://github.com/rstyczynski/umc

# License
I have no idea, but reuse and modify as you wish. The only thing is to add notice about source of the code.


