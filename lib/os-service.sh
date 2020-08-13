#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

service_type=$(basename "$0" | cut -d. -f1)

export umc_home=$script_dir/..
export umc_bin=$umc_home/bin
source $umc_home/bin/umc.h

export umc_cfg=~/.umc
export umc_run=$umc_cfg/pid; mkdir -p $umc_run

case $umc_home in
    /opt/umc)
        #
        # runs from central location? 
        # use central log and obd locations unless other cfg is in ~/.umc/umc.conf 
        #
        if [ -z $umc_log ]; then
            export umc_log=/var/log/umc
            sudo mkdir -p $umc_log
            sudo chmod 777 $umc_log
        fi

        if [ -z $status_root ]; then
            export status_root=/run/umc/obd
            # prepare odb directory, as /run is a ramdisk directories must be recreated after boot
            sudo mkdir -p /run/umc/obd
            sudo chmod 777 /run/umc
            sudo chmod 777 /run/umc/obd
        fi

        ;;
    *)
        #
        # runs in other location? 
        # use home directory
        #
        if [ -z $umc_log ]; then
            export umc_log=~/umc/log
            mkdir -p $umc_log
        fi

        if [ -z $status_root ]; then
            export status_root=~/umc/obd
            mkdir -p $status_root
        fi
            
        ;;
esac

function usage() {
    cat <<EOF
Usage: $service_type svc_def [start|stop|status|restart|register|unregister] 
EOF
}

umc_svc_def=$1

os_release=$(cat /etc/os-release | grep '^VERSION=' | cut -d= -f2 | tr -d '"' | cut -d. -f1)
if [ $os_release -eq 6 ]; then
    source /etc/init.d/functions
fi

case $2 in
start | stop | status | restart | register | unregister)
    operation=$2
    shift
    ;;
*)
    usage
    exit 1
    ;;
esac

if [ ! $umc_cfg/$umc_svc_def ]; then
    echo "Error. Service definition not found."
    exit 1
fi


svc_name=$(echo $umc_svc_def | cut -d. -f1)

function y2j() {
    python -c "import json, sys, yaml ; y=yaml.safe_load(sys.stdin.read()) ; print(json.dumps(y))"
}

function start() {

    for system in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r "keys[]"); do
        echo $system
        for subsystem in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os | keys[]"); do
            echo "- $subsystem"

            keys=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem[] | keys[]" 2>/dev/null)
            if [ ! -z "$keys" ]; then
                for component in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem | keys[]"); do
                    echo "    - $subsystem-$component"
                    case $subsystem-$component in
                    disk-space)
                        mount_cnt=0
                        for mount_point_id in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space | keys[]"); do
                            mount_point_name=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space[$mount_point_id].name")
                            mount_point=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space[$mount_point_id].point")
                            echo "       - $mount_point_name-$mount_point"
                            (
                                umc df collect 15 5760 $mount_point |
                                    $umc_bin/csv2obd --resource disk-space-$mount_point_name |
                                    $umc_bin/logdirector.pl -dir $umc_log -addDateSubDir -name disk-space-$mount_point_name -detectHeader -checkHeaderDups -flush -tee |
                                    $umc_bin/dvdt --resource disk-space-$mount_point_name --dataat 8 |
                                    $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name disk-space-$mount_point_name\_dt -detectHeader -checkHeaderDups -flush
                            ) &
                            echo $! >>$umc_run/$svc_name.pid
                            mount_cnt=$(( $mount_cnt + 1 ))
                        done
                        ;;
                    disk-tps)
                        disk_cnt=0
                        for key in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component | keys[]"); do
                            dev_name=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[$key].name")
                            dev_device=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[$key].device")
                            echo "       - $dev_name-$dev_device"
                            (
                                umc iostat collect 5 2147483647 $dev_device |
                                    $umc_bin/csv2obd --resource disk-tps-$dev_name |
                                    $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name disk-tps-$dev_name -detectHeader -checkHeaderDups -flush
                            ) &
                            echo $! >>$umc_run/$svc_name.pid
                            disk_cnt=$(( $disk_cnt + 1 ))
                        done
                        ;;                    
                    network-if)
                        net_cnt=0
                        for key in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component | keys[]"); do
                            dev_name=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[$key].name")
                            dev_device=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[$key].device")
                            echo "       - $dev_name-$dev_device"
                            (
                                umc ifconfig collect 5 2147483647 $dev_device |
                                    $umc_bin/csv2obd --resource network-if-$dev_name |
                                    $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name network-if-$dev_name -detectHeader -checkHeaderDups -flush -tee |
                                    $umc_bin/dvdt --resource network-if-$dev_name --dataat 7 |
                                    $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name network-if-$dev_name\_dt -detectHeader -checkHeaderDups -flush
                            ) &
                            echo $! >>$umc_run/$svc_name.pid
                            net_cnt=$(( $net_cnt + 1 ))
                        done
                        ;;
                    network-tcp)
                        for key in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[]"); do
                            echo "       - $key"
                            if [ $key == "stats" ]; then
                                (
                                    umc netstattcp collect 5 2147483647 |
                                        $umc_bin/csv2obd --resource network-tcp-netstattcp |
                                        $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name network-tcp-netstattcp -detectHeader -checkHeaderDups -flush -tee |
                                        $umc_bin/dvdt --resource network-tcp-netstattcp --dataat 7 |
                                        $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name network-tcp-netstattcp\_dt -detectHeader -checkHeaderDups -flush
                                ) &
                                echo $! >>$umc_run/$svc_name.pid
                            fi
                        done
                        ;;
                    esac
                done
            else
                for component in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem[]"); do

                    echo "  - $subsystem-$component"
                    case $subsystem-$component in
                    system-vmstat)
                        (
                            umc vmstat collect 5 2147483647 |
                                $umc_bin/csv2obd --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component -detectHeader -checkHeaderDups -flush
                        ) &
                        echo $! >>$umc_run/$svc_name.pid
                        ;;
                    system-uptime)
                        (
                            umc uptime collect 5 2147483647 |
                                $umc_bin/csv2obd --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component -detectHeader -checkHeaderDups -flush
                        ) &
                        echo $! >>$umc_run/$svc_name.pid
                        ;;
                    memory-meminfo)
                        (
                            umc meminfo collect 5 2147483647 |
                                $umc_bin/csv2obd --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component -detectHeader -checkHeaderDups -flush -tee |
                                $umc_bin/dvdt --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component\_dt -detectHeader -checkHeaderDups -flush
                        ) &
                        ;;
                    memory-free)
                        (
                            umc free collect 5 2147483647 |
                                $umc_bin/csv2obd --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component -detectHeader -checkHeaderDups -flush -tee |
                                $umc_bin/dvdt --resource $subsystem-$component |
                                $umc_bin/logdirector.pl -addDateSubDir -dir $umc_log -name $subsystem-$component\_dt -detectHeader -checkHeaderDups -flush
                        ) &
                        ;;
                    esac
                done
            fi
        done

        cat >$umc_log/os_$system.html <<EOF
<meta http-equiv="Refresh" content="0; url='/umc/log/charts_os?disk_cnt=$disk_cnt&net_cnt=$net_cnt&mount_cnt=$mount_cnt'" />
EOF

    done

}

function stop() {
    if [ -f $umc_run/$svc_name.pid ]; then
        echo -n ">> stopping service $svc_name"
        for tmp_umc_pid in $(cat $umc_run/$svc_name.pid); do
            sudo $umc_bin/killtree.sh $tmp_umc_pid >/dev/null
            echo -n "."
        done
        rm -f $umc_run/$svc_name.pid
        echo "Stopped."
    fi
}

function register_inetd() {
    cat >/tmp/umc_$service_type-$svc_name <<EOF
#!/bin/bash
#
# chkconfig:   12345 01 99
# description: umc $service_type for $svc_name
#
sudo su - $(whoami) $umc_home/lib/$service_type.sh $svc_name.yml \$1
EOF

    chmod +x /tmp/umc_$service_type-$svc_name
    sudo mv /tmp/umc_$service_type-$svc_name /etc/init.d/umc_$service_type-$svc_name

    sudo chkconfig --add umc_$service_type-$svc_name

    echo echo "Service registered. Start the service:"
    cat <<EOF
sudo service umc_$service_type-$svc_name start
sudo service umc_$service_type-$svc_name status
sudo service umc_$service_type-$svc_name stop
EOF
}

function unregister_inetd() {

    stop
    sudo chkconfig --del umc_$service_type-$svc_name
    sudo rm -f /etc/init.d/umc_$service_type-$svc_name

    echo "Service unregistered."
}

function register_systemd() {

    sudo cat >/etc/systemd/system/umc_$service_type-$svc_name.service <<EOF
[Unit]
Description=umc data collector - $service_type - $svc_name

[Service]
User=$(whomai)
TimeoutStartSec=infinity

ExecStart=$umc_root/lib/$service_type.sh $svc_name start
ExecStop=$umc_root/lib/$service_type.sh $svc_name stop

Restart=always
RemainAfterExit=yes
  
[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable umc_$service_type-$svc_name.service

    echo "Service registered. Start the service:"
    cat <<EOF
sudo systemctl start umc_$service_type-$svc_name.service
sudo systemctl restart umc_$service_type-$svc_name.service
sudo systemctl stop umc_$service_type-$svc_name.service
sudo cat /var/log/messages
EOF

}

function unregister_systemd() {

    stop
    sudo systemctl disable umc_$service_type-$svc_name.service
    sudo rm -f /etc/systemd/system/umc_$service_type-$svc_name.service

    sudo systemctl daemon-reload

    echo "Service unregistered."
}

case $operation in
start)
    if [ ! -f $umc_run/$svc_name.pid ]; then
        start
    else
        echo "Already running. Info: $(cat $umc_run/$svc_name.pid)"
        exit 1
    fi
    ;;
stop)
    stop
    ;;
status)
    if [ ! -f $umc_run/$svc_name.pid ]; then
        echo "Not running"
        exit 1
    else
        echo "Running. Info: $(cat $umc_run/$svc_name.pid)"
    fi
    ;;
restart)
    stop
    sleep 1
    start
    ;;
register)
    case $os_release in
    6)
        register_inetd
        ;;
    7)
        register_systemd
        ;;
    esac
    ;;
unregister)
    case $os_release in
    6)
        unregister_inetd
        ;;
    7)
        unregister_systemd
        ;;
    *)
        echo Error. Unsupported OS release.
        exit 1
        ;;
    esac
    ;;
*)
    exit 1
    ;;
esac
