#---------------------------------------------------------------------------------------
#--- platform location & specific configuration
#---------------------------------------------------------------------------------------

export FMW_MOME=/oracle/fmwhome
export WLS_HOME=$FMW_MOME/wlserver_10.3/server
export SOA_HOME=$FMW_MOME/Oracle_SOA1
export DOMAIN_HOME=/oracle/fmwhome/user_projects/domains/dev_soasuite

#---------------------------------------------------------------------------------------
#--- platform elements 
#---------------------------------------------------------------------------------------

. $WLS_HOME/bin/setWLSEnv.sh

#---------------------------------------------------------------------------------------
#--- reporting
#---------------------------------------------------------------------------------------

export CSVdelimiter=,

#---------------------------------------------------------------------------------------
#--- platform version
#---------------------------------------------------------------------------------------

# use in code: cmd_version=$(eval "echo $(echo \$$cmd\_version)"); echo $cmd_version
#              cmd_version_major=$(eval "echo $(echo \$$cmd\_version_major)"); echo $cmd_version_major

#2.6.39-400.109.5.el6uek.x86_64
export linux_version=$(uname -r | cut -d'-' -f1)
export linux_version_major=$(uname -r | cut -d'-' -f1 | cut -d'.' -f1)
export linux_version_minor=$(uname -r | cut -d'-' -f1 | cut -d'.' -f2)
export linux_version_patch=$(uname -r | cut -d'-' -f1 | cut -d'.' -f3)
export linux_version_specific=$(uname -r | cut -d'-' -f2-999)
    
#1.6.0_37, 1.8.0_60
export java_version=$($JAVA_HOME/bin/java -version 2>&1 | grep 'java version'  | cut -d' ' -f3 | tr -d '"')
export java_version_major=$(echo $java_version | cut -f1 -d'_' | cut -d'.' -f1)
export java_version_minor=$(echo $java_version | cut -f1 -d'_' | cut -d'.' -f2)
export java_version_patch=$(echo $java_version | cut -f1 -d'_' | cut -d'.' -f3)
export java_version_specific=$(echo $java_version | cut -f2 -d'_')
    
#10.3.6.0
export wls_version=$(cat $FMW_MOME/registry.xml | grep 'component name="WebLogic Server"' | tr ' ' '\n' | grep version | cut -d'=' -f2 | tr -d '"')
export wls_version_major=$(echo $wls_version | cut -d'.' -f1)
export wls_version_minor=$(echo $wls_version | cut -d'.' -f2)
export wls_version_patch=$(echo $wls_version | cut -d'.' -f3)
export wls_version_specific=$(echo $wls_version | cut -d'.' -f4)
    
#11.1.1.7.0
export soa_version=$($SOA_HOME/bin/soaversion.sh | grep "Oracle SOA Server version" | cut -d' ' -f5)
export soa_version_major=$(echo $soa_version | cut -d'.' -f1)
export soa_version_minor=$(echo $soa_version | cut -d'.' -f2)
export soa_version_patch=$(echo $soa_version | cut -d'.' -f3)
export soa_version_specific=$(echo $soa_version | cut -d'.' -f4-5)
    
#---------------------------------------------------------------------------------------
#--- tools category
#---------------------------------------------------------------------------------------


export platformLayers="hardware/linux/java/wls/soa"
    
export system_type=$(uname -s | tr [A-Z] [a-z])

export linux_layer=hardware
export java_layer=linux
export wls_layer=java
export soa_layer=wls    
export soabindings_layer=soa

export vmstat_layer=$system_type
export free_layer=$system_type
export top_layer=$system_type
export uptime_layer=$system_type
export meminfo_layer=$system_type
export tcpext_layer=$system_type
export netstat_tcp_layer=$system_type
export ifconfig_layer=$system_type
export iostat_layer=$system_type
    
#---------------------------------------------------------------------------------------
#--- tools version
#---------------------------------------------------------------------------------------

# use in code: cmd_version=$(eval "echo $(echo \$$cmd\_version)"); echo $cmd_version

# procps
export vmstat_package=procps/$(vmstat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export free_package=procps/$(free -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export top_package=procps/$(top -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export uptime_package=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

#--files from /proc
export meminfo_package=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export tcpext_package=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

# net-tools
export netstat_tcp_package=net-tools/$(netstat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export ifconfig_package=net-tools/$(ifconfig -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

# sysstat
export iostat_package=systat/$(iostat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
