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

# Installation
To install UMC in a current directory execute below one-liner. It will create umc directory, get UMC from github, and initialize it.

```bash
mkdir umc; cd umc; curl  -Lk https://api.github.com/repos/rstyczynski/umc/tarball/master | tar -xz --strip=1; cd ..; . umc/bin/umc.h
```

Now you are ready to use UMC on Linux.


# First time use
Before use one have to source umc.h which adds command line functions to Bash environment. Apart of internal things, UMC extends classpath by SOA and OSB jars, and calls Oracle Miffleware environment confguration script.

```bash
. umc/bin/umc.h 

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

# List available sensors
To list available probes, execute umc with sensors paramter

```bash
umc sensors

vmstat free top uptime meminfo tcpext netstattcp ifconfig iostat soabindings businessservice
```

It means that this version of UMC is shipped with wide range of Linux probes, and two probes for SOA: one for OSB, and the other one for Composite.

# Configuration of Oracle Middleware
To configure UMC for Oracle Middleware, edit etc/umc.cfg to provide required information about home and domain directories. Note that prividing WebLogic domain directory is important, as UMC probes are started from domain directory to bypass a need of authentication. 

```bash
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
Availability of probes does not mean that all of them will work. Packages may be missing in the Operating system or system may be host different version of utilities. To validate compatibility of tools UMC does two things: (a) checks general availability with known OS level technique, and calls the uyility to get returned headers to compare with signature stored in plugin meat-information. UMC 

```bash
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
1. install misising package
2. configure Oracle Midlleware directories in etc/umc.cfg

In the worst case you need to prepare new version of probe. It's descibed in separated part of the manual.


# First data collection
Now your UMC is ready to do data collection. Let's play with iostat.

Regular iostat returns nice looking, but not very useful for data collection output.

```bash
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

With UMC you get less nice, but more ready for automerted processing reposnse

```bash
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


# TODO Tools
1. Ping
2. Add node column to identify process e.g. WebLogic instance on a host
3. Add long timestamp (raw long value of Linux time) as a generic column
4. Add version information: os, utils
5. switch iostat into extended mode

# TODO General
1. Automatically execute test for given OS with '0' level utilities. Once executed stores information in directory that test was passed or failed. Invoke should use this information.
2. Invoke performs header test upon first run to write result to files. During next runs it's verified if test was passed or not.
3. Add "procps version" e.g. free -V to validate comatibility of tools and scripts
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
