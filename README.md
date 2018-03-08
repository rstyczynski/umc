# Universal Metric Collector

# Rationale
Operating systems are shipped with various set of tools to get certain system metrics. Moreover the same operating system in different versions may be shipped with toolset giving slightly different output. Some of tools are able to run in a loop for defined time and interval, others can't. In such environment it's not possible to relay on the regular tools, without ensuring that all of them are returning data in expected format, during predefined period with pgiven interval. Such insurance is required when other tools are relaying on data produced by tools - e.g. monitoring layer. 

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
To list available probes, execute umc with sensors paramter

```
umc sensors

vmstat free top uptime meminfo tcpext netstattcp ifconfig iostat soabindings businessservice
```

It means that this version of UMC is shipped with wide range of Linux probes, and two probes for SOA: one for OSB, and the other one for Composite.

# Configuration of Oracle Middleware
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

```
umc iostat collect 1 2

datetime,timezone,timestamp,system,source,Device,tps,kB_read/s,kB_wrtn/s,kB_read,kB_wrtn
2018-02-28 00:30:22,-0800,1519806622,soabpm-vm.site,iostat,sdb,1.56,2.27,10.65,699558,3288220
2018-02-28 00:30:22,-0800,1519806622,soabpm-vm.site,iostat,dm-0,0.88,1.27,7.82,392265,2412892
2018-02-28 00:30:22,-0800,1519806622,soabpm-vm.site,iostat,dm-1,0.45,0.62,1.19,192084,368136
2018-02-28 00:30:22,-0800,1519806623,soabpm-vm.site,iostat,sda,0.00,0.00,0.00,0,0
2018-02-28 00:30:22,-0800,1519806623,soabpm-vm.site,iostat,sdc,3.00,0.00,36.00,0,36
2018-02-28 00:30:22,-0800,1519806623,soabpm-vm.site,iostat,sdb,2.00,0.00,16.00,0,16
2018-02-28 00:30:22,-0800,1519806623,soabpm-vm.site,iostat,dm-0,0.00,0.00,0.00,0,0
2018-02-28 00:30:22,-0800,1519806623,soabpm-vm.site,iostat,dm-1,0.00,0.00,0.00,0,0
2018-02-28 00:30:24,-0800,1519806624,soabpm-vm.site,iostat,sda,0.00,0.00,0.00,0,0
2018-02-28 00:30:24,-0800,1519806624,soabpm-vm.site,iostat,sdc,0.00,0.00,0.00,0,0
2018-02-28 00:30:24,-0800,1519806624,soabpm-vm.site,iostat,sdb,2.00,0.00,4.00,0,4
2018-02-28 00:30:24,-0800,1519806624,soabpm-vm.site,iostat,dm-0,0.00,0.00,0.00,0,0
2018-02-28 00:30:24,-0800,1519806624,soabpm-vm.site,iostat,dm-1,0.00,0.00,0.00,0,0
```

Notice change from Blk to kB, it's done by regular iostat parameter. Newer versions of iostat report performance using kB. 

# Oracle Middleware
UMC collects data from: WebLogic, OSB, and SOA composite. WebLogic data is collected trough regular mBeans, OSB via wlst, and SOA uses DMS subsystem available in WebLogic. 

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
```
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


# Missing utility
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
UMC is based mainly on bash, however requires set of packages to work properly. Python and perl are used by utility scripts supporting UMC in some aspects as reading yaml configuration, or prefixing stream with timestamps.

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


