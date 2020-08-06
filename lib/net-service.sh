#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

service_type=$(basename "$0" | cut -d. -f1)

export umc_home=$script_dir/..
export umc_bin=$umc_home/bin
export umc_cfg=$umc_home/../.umc
export umc_log=/var/log/umc
export umc_run=$umc_cfg/pid
mkdir -p $umc_run

source $umc_home/bin/umc.h

function usage() {
    cat <<EOF
Usage: net_prob.sh svc_def [start|stop|status|restart|register] 
EOF
}

umc_svc_def=$1

os_release=$(cat /etc/os-release | grep '^VERSION=' | cut -d= -f2 | tr -d '"' | cut -d. -f1)

if [ $os_release -eq 6 ]; then
    source /etc/init.d/functions
fi

case $2 in
start | stop | status | restart | register)
    operation=$2
    shift
    ;;
*)
    usage
    exit 1
    ;;
esac

if [ ! $umc_cfg/$umc_svc_def ]; then
    echo "Error. Service definitino not found."
    exit 1
fi


# umc obd; is here as /run is a ramdisk
export status_root=/run/umc/obd
# prepare odb directory
sudo mkdir -p /run/umc/obd
sudo chmod 777 /run/umc
sudo chmod 777 /run/umc/obd


svc_name=$(echo $umc_svc_def | cut -d. -f1)

function y2j() {
    python -c "import json, sys, yaml ; y=yaml.safe_load(sys.stdin.read()) ; print(json.dumps(y))"
}

function start() {

    for service_name in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".network[] | keys[]"); do

        for target_name in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.tcp[] | keys[]"); do

            address=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.tcp[].$target_name.ip" | grep -v null)

            echo $service_name $target_name $address

            (
                umc pingSocket collect 15 5760 --subsystem $address |
                    $umc_bin/csv2obd --resource socket_$service_name-$target_name |
                    $umc_bin/logdirector.pl -dir /var/log/umc -addDateSubDir -name socket_$service_name-$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umc_run/$svc_name.pid

        done

        # icmp
        for target_name in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[] | keys[]"); do

            address=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[].$target_name.ip" | grep -v null)

            echo $service_name $target_name $address

            (
                umc ping collect 15 5760 $address |
                    $umc_bin/csv2obd --resource ping_$service_name-$target_name |
                    $umc_bin/logdirector.pl -dir /var/log/umc -addDateSubDir -name ping_$service_name-$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umc_run/$svc_name.pid

            (
                umc mtr collect 5 288 $address |
                    $umc_bin/csv2obd --resource mtr_$service_name-$target_name |
                    $umc_bin/logdirector.pl -dir /var/log/umc -addDateSubDir -name mtr_$service_name-$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umc_run/$svc_name.pid
        done

        cat >$umc_log/ping_$service_name.html <<EOF
<meta http-equiv="Refresh" content="0; url='/umc/log/ping?service_name=$service_name'" />
EOF
        cat >$umc_log/socket_$service_name.html <<EOF
<meta http-equiv="Refresh" content="0; url='/umc/log/socket?service_name=$service_name'" />
EOF
        cat >$umc_log/network_$service_name.html <<EOF
<meta http-equiv="Refresh" content="0; url='/umc/log/network?service_name=$service_name'" />
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
        rm $umc_run/$svc_name.pid
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
$umc_home/lib/$service_type.sh $svc_name.yml \$1
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


case $operation in
start)
    if [ ! -f $umc_run/$umc_svc_def.pid ]; then
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


