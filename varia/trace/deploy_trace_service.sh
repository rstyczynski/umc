#!/bin/bash

if [ ! -d /opt/umc ]; then
    echo "Error. deploy_trace_service.sh is intended to run with root vrsion of umc, but /opt/umc is not available. Install root umc or consider using user space deploy_trace.sh"
    exit 1
fi

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

os_release=$(cat /etc/os-release | grep '^VERSION=' | cut -d= -f2 | tr -d '"' | cut -d. -f1)

echo "#"
echo "# copy resource definitions"
echo "#"

rm ~/.umc/os-probe_*.yml
cp $shared_trace_root/cfg/$server_env/$server_type/os-probe_$server_env\-$server_type.yml ~/.umc

rm ~/.umc/net-probe_*.yml
cp $shared_trace_root/cfg/$server_env/ext/net-probe_*.yml ~/.umc

echo "#"
echo "# create umc.conf"
echo "#"

mkdir -p ~/.umc
mv ~/.umc/umc.conf ~/.umc/umc.conf.bak
cat > ~/.umc/umc.conf <<EOF
export umc_log=/var/log/umc
export status_root=/run/umc/obd

export server_env=$server_env
export server_type=$server_type
export shared_trace_root=$shared_trace_root
EOF

echo "#"
echo "# update bash_profile"
echo "#"

cp ~/.bash_profile ~/.bash_profile.bak
cat ~/.bash_profile.bak | sed '/# umc envs. - START/,/# umc envs. - STOP/d'  > ~/.bash_profile

cat >> ~/.bash_profile <<EOF
# umc envs. - START

source ~/.umc/umc.conf

mkdir -p $status_root
mkdir -p $umc_log
mkdir -p $shared_trace_root/$server_env/$(hostname)/runtime/obd
mkdir -p $shared_trace_root/$server_env/$(hostname)/runtime/log

# umc envs. - STOP
EOF
cat ~/.bash_profile
source ~/.bash_profile

echo "#"
echo "# unregister services"
echo "#"
os_service=os-probe_$server_env\-$server_type.yml
/opt/umc/lib/os-service.sh $os_service unregister

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
    /opt/umc/lib/net-service.sh $net_service unregister
done

echo $(ps aux | grep umc | grep -v grep | wc -l)
sleep 2
echo $(ps aux | grep umc | grep -v grep | wc -l)
if [ "$(ps aux | grep umc | grep -v grep | wc -l)" != "0" ]; then
    echo "Error. umc processes left after unregister. Check and fix this. Cannot contine."
    exit 2
fi

echo "#"
echo "# register services"
echo "#"
os_service=os-probe_$server_env\-$server_type.yml
/opt/umc/lib/os-service.sh $os_service register

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
    /opt/umc/lib/net-service.sh $net_service register
done

echo "#"
echo "# update cron"
echo "#"

echo "# start - umc" > cron.tmp
os_service=os-probe_$server_env\-$server_type.yml
service_name=$(echo $os_service | cut -f1 -d.)
case $os_release in
6)
    echo "1 0 * * * sudo service umc_os-service-$service_name restart" >> cron.tmp
    ;;
7)
    echo not supported
    exit 3
    ;;
esac

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
    service_name=$(echo $net_service | cut -f1 -d.)

    case $os_release in
    6)
        echo "1 0 * * * sudo service umc_net-service-$service_name restart" >> cron.tmp
        ;;
    7)
        echo not supported
        exit 3
        ;;
    esac 
done
echo "* * * * * ~/umc/varia/trace/rsync_trace.sh $server_env $server_type $shared_trace_root" >>  cron.tmp
echo "# stop - umc" >>  cron.tmp

(crontab -l 2>/dev/null |
sed '/# start - umc/,/# stop - umc/d'
cat cron.tmp) | crontab -; rm cron.tmp; crontab -l

echo "#"
echo "# start umc metric collection services"
echo "#"

os_service=os-probe_$server_env\-$server_type.yml
service_name=$(echo $os_service | cut -f1 -d.)
case $os_release in
6)
    sudo service umc_os-service-$service_name start
    ;;
7)
    echo not supported
    exit 3
    ;;
esac
sudo service umc_os-service-$service_name start

for net_service in $(cd ~/.umc; ls net-probe_*.yml); do 
    service_name=$(echo $net_service | cut -f1 -d.)
    case $os_release in
    6)
        sudo service umc_net-service-$service_name start
        ;;
    7)
        echo not supported
        exit 3
        ;;
    esac
done

echo "#"
echo "# perform intial rsync"
echo "#"
/opt/umc/varia/trace/rsync_trace.sh $server_env $server_type $shared_trace_root

echo "#"
echo "# look at service"
echo "#"
read -p "Press enter to see umc services"
    case $os_release in
    6)
        sudo chkconfig --list | grep umc
        ;;
    7)
        echo not supported
        exit 3
        ;;
    esac

echo "#"
echo "# look at cron"
echo "#"
read -p "Press enter to see crontab"
crontab -l

echo "#"
echo "# look at logs"
echo "#"

read -p "Press enter to see local logs"
ll ~/trace/log
ll ~/trace/log/$(date +%Y-%m-%d)

read -p "Press enter to see central logs"
ll $shared_trace_root/$server_env/$(hostname)/runtime/log
ls $shared_trace_root/$server_env/$(hostname)/runtime/log/$(date +%Y-%m-%d)

echo "#"
echo "# look at state data"
echo "#"
read -p "Press enter to see local state file"
ll ~/trace/obd
cat ~/trace/obd/system-vmstat/state

read -p "Press enter to see central state file"
ll $shared_trace_root/$server_env/$(hostname)/runtime/obd
cat $shared_trace_root/$server_env/$(hostname)/runtime/obd/system-vmstat/state
