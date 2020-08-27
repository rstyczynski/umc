#!/bin/bash

if [ -z "$shared_trace_root" ] || [ -z "$server_env" ] || [ -z "$server_type" ]; then
    echo "Usage: config_trace.sh 
, with exported veriables: server_env, server_type, shared_trace_root"
    return 1
fi

if [ ! -d $shared_trace_root ]; then
    echo "Error! Shared directory does not exist: $shared_trace_root"
    return 2
fi

if [ ! -d $shared_trace_root/cfg/$server_env/$server_type ]; then
    echo "Error! Server directory does not exist: $shared_trace_root/cfg/$server_env/$server_type"
    return 3
fi

if [ $(ls $shared_trace_root/cfg/$server_env/$server_type/os-probe_$server_env\-$server_type.yml | wc -l) -eq 0 ]; then
    echo "Error! OS resource definition deas not exist at $shared_trace_root/cfg/$server_env/$server_type/os-probe_$server_env\-$server_type.yml"
    return 4
fi

if [ $(ls $shared_trace_root/cfg/$server_env/ext/net-probe_*.yml | wc -l) -eq 0 ]; then
    echo "Error! Network resource definition deas not exist at $shared_trace_root/cfg/$server_env/ext/net-probe_*.yml"
    return 4
fi

#
echo copy resource definitions...
#
cp $shared_trace_root/cfg/$server_env/$server_type/os-probe_$server_env\-$server_type.yml ~/.umc
cp $shared_trace_root/cfg/$server_env/ext/net-probe_*.yml ~/.umc

#
echo update bash_profile
#
cp ~/.bash_profile ~/.bash_profile.bak
cat ~/.bash_profile.bak | sed '/# umc envs. - START/,/# umc envs. - STOP/d'  > ~/.bash_profile

cat >> ~/.bash_profile <<EOF
# umc envs. - START

export server_env=$server_env
export server_type=$server_type

# keep as is
export status_root=~/trace/obd
export umc_log=~/trace/log

mkdir -p ~/.umc
mkdir -p $status_root
mkdir -p $umc_log
mkdir -p $shared_trace_root/$server_env/$(hostname)/runtime/obd
mkdir -p $shared_trace_root/$server_env/$(hostname)/runtime/log

# umc envs. - STOP
EOF
cat ~/.bash_profile
source ~/.bash_profile

#
echo update cron...
#
echo "# start - umc" > cron.tmp
os_service=os-probe_$server_env\-$server_type.yml
echo "1 0 * * * ~/umc/lib/os-service.sh $os_service restart" >> cron.tmp

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
  echo "1 0 * * * ~/umc/lib/net-service.sh $net_service restart" >> cron.tmp
done
echo "* * * * * rsync -rt ~/trace/obd/ \$shared_trace_root/\$server_env/\$(hostname)/runtime/obd" >>  cron.tmp
echo "* * * * * rsync -rt ~/trace/log/ \$shared_trace_root/\$server_env/\$(hostname)/runtime/log" >>  cron.tmp
echo "# stop - umc" >>  cron.tmp

(crontab -l 2>/dev/null |
sed '/# start - umc/,/# stop - umc/d'
cat cron.tmp) | crontab -; rm cron.tmp; crontab -l

#
echo start umc metric collection services...
#
source ~/.bash_profile

os_service=os-probe_$server_env\-$server_type.yml
~/umc/lib/os-service.sh $os_service stop
nohup ~/umc/lib/os-service.sh $os_service start block > $os_service.log & 

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
  ~/umc/lib/net-service.sh $net_service stop
  nohup ~/umc/lib/net-service.sh $net_service start block > $net_service.log &
done

#
echo test log and state data...
#
ll ~/trace/log
ll $shared_trace_root/$server_env/$(hostname)/runtime/log

ll ~/trace/obd
ll $shared_trace_root/$server_env/$(hostname)/runtime/obd