#/bin/bash

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

if [ ! $umccfg/$umc_svc_def ]; then
    echo "Error. Service definitino not found."
    exit 1
fi

umc_home=~/umc
umccfg=~/.umc
umc_log=/var/log/umc

source $umc_home/bin/umc.h

umc_pid=$umccfg/pid
mkdir -p $umc_pid

svc_name=$(echo $umc_svc_def | cut -d. -f1)

function y2j() {
    python -c "import json, sys, yaml ; y=yaml.safe_load(sys.stdin.read()) ; print(json.dumps(y))"
}

function start() {
    for service_name in $(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[] | keys[]"); do

        for target_name in $(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.tcp[] | keys[]"); do

            address=$(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.tcp[].$target_name.ip" | grep -v null)

            echo $service_name $target_name $address

            (
                umc pingSocket collect 15 5760 --subsystem $address |
                    csv2obd --resource socket_$service_name\_$target_name |
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name socket_$service_name\_$target_name -detectHeader -statusHeaderDups -flush
            ) &
            echo $! >>$umc_pid/$umc_svc_def.pid

        done

        # icmp
        for target_name in $(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[] | keys[]"); do

            address=$(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[].$target_name.ip" | grep -v null)

            echo $service_name $target_name $address

            (
                umc ping collect 15 5760 $address |
                    csv2obd --resource ping_$service_name\_$target_name |
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name ping_$service_name\_$target_name -detectHeader -statusHeaderDups -flush
            ) &
            echo $! >>$umc_pid/$umc_svc_def.pid

            (
                umc mtr collect 300 288 $address |
                    csv2obd --resource mtr_$service_name\_$target_name |
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name mtr_$service_name\_$target_name -detectHeader -statusHeaderDups -flush
            ) &
            echo $! >>$umc_pid/$umc_svc_def.pid
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
    for umc_pid in $(cat $umc_pid/$umc_svc_def.pid); do
        killtree.sh $umc_pid
    done
    rm $umc_pid/$umc_svc_def.pid
}


function register_inetd() {
    cat >/tmp/umc_net-probe_$svc_name <<EOF
#!/bin/bash
$umc_home/lib/net_probe.sh $svc_name \$1
EOF

chmod +x /tmp/umc_net-probe_$svc_name 
sudo mv /tmp/umc_net-probe_$svc_name /etc/init.d/umc_net-probe_$svc_name

    echo "Service registered. Execute to enable, start, etc:"
    cat <<EOF
chkconfig --add umc_net-probe_$svc_name 
chkconfig --level 2345 umc_net-probe_$svc_name on 
EOF
}

function register_systemd() {

    sudo cat >/etc/systemd/system/umc_net-probe_$svc_name.service <<EOF
[Unit]
Description=umc data collector - net_probe - $svc_name

[Service]
User=$(whomai)
TimeoutStartSec=infinity

ExecStart=$umc_root/lib/net_probe.sh $svc_name start
ExecStop=$umc_root/lib/net_probe.sh $svc_name stop

Restart=always
RemainAfterExit=yes
  
[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload

    echo "Service registered. Execute to enable, start, etc:"
    cat <<EOF
sudo systemctl enable umc_net-probe_$svc_name.service
sudo systemctl restart umc_net-probe_$svc_name.service
sudo cat /var/log/messages
EOF

}



case $operation in
start)
    if [ ! -f $umc_pid/$umc_svc_def.pid ]; then
        start
    else
        echo "Already running. Info: $(cat $umc_pid/$umc_svc_def.pid)"
        exit 1
    fi
    ;;
stop)
    stop
    ;;
status)
    if [ ! -f $umc_pid/$umc_svc_def.pid ]; then
        echo "Not running"
        exit 1
    else
        echo "Running. Info: $(cat $umc_pid/$umc_svc_def.pid)"
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


