export CSVdelimiter=,


#---
#--- tools version
#---

#
# use in code: cmd_version=$(eval "echo $(echo \$$cmd\_version)"); echo $cmd_version
#

# procps
export vmstat_version=procps/$(vmstat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export free_version=procps/$(free -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export top_version=procps_$(top -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export uptime_version=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

#--files from /proc
export meminfo_version=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export tcpext_version=procps/$(uptime -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

# net-tools
export netstat_tcp_version=net-tools/$(netstat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')
export ifconfig_version=net-tools/$(ifconfig -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')

# sysstat
export iostat_version=systat/$(iostat -V  2>&1 | head -1 | sed 's/[^0-9.]*//g')





