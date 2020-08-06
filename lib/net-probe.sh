#/bin/bash

function usage () {
    cat <<EOF
Usage: net_prob.sh svc_def [start|stop|check|restart] 
EOF
}

umc_svc_def=$1

case $2 in
start|stop|check|restart) 
    operation=$2; shift
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

umccfg=~/.umc
umc_log=/var/log/umc

umcpid=$umccfg/pid
mkdir -p $umcpid


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
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name socket_$service_name\_$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umcpid/$umc_svc_def.pid

        done

        # icmp
        for target_name in $(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[] | keys[]"); do

            address=$(cat $umccfg/$umc_svc_def | y2j | jq -r ".network[].$service_name.icmp[].$target_name.ip" | grep -v null)

            echo $service_name $target_name $address

            (
                umc ping collect 15 5760 $address |
                    csv2obd --resource ping_$service_name\_$target_name |
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name ping_$service_name\_$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umcpid/$umc_svc_def.pid

            (
                umc mtr collect 300 288 $address |
                    csv2obd --resource mtr_$service_name\_$target_name |
                    logdirector.pl -dir /var/log/umc -addDateSubDir -name mtr_$service_name\_$target_name -detectHeader -checkHeaderDups -flush
            ) &
            echo $! >>$umcpid/$umc_svc_def.pid
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
    for umc_pid in $(cat $umcpid/$umc_svc_def.pid); do
        killtree.sh $umc_pid
        rm $umcpid/$umc_svc_def.pid
    done
}

case $operation in
start)
    if [ ! -f $umcpid/$umc_svc_def.pid ]; then
        start
    else
        echo "Already running. Info: $(cat $umcpid/$umc_svc_def.pid)"
        return 1
    fi
    ;;
stop)
    stop
    ;;
check)
    if [ ! -f $umcpid/$umc_svc_def.pid ]; then
        echo "Not running"
        return 1
    else
        echo "Running. Info: $(cat $umcpid/$umc_svc_def.pid)"
    fi
    ;;
restart)
    stop
    sleep 1
    start
    ;;
*)
    exit 1
    ;;
esac

