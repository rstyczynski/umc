#/bin/bash

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
Usage: $service_type svc_def [start|stop|status|restart|register] 
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
    echo "Error. Service definition not found."
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


for system in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r "keys[]"); do
    echo $system
    for subsystem in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os | keys[]"); do
        echo "- $subsystem"
        
        keys=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem[] | keys[]" 2>/dev/null) 
        if [ ! -z "$keys" ]; then
            for component in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem | keys[]"); do
                    echo "    - $subsystem\-$component"
                    case $subsystem\-$component in
                    disk:space)
                        for mount_point_id in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space | keys[]"); do
                            mount_point_name=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space[$mount_point_id].name")
                            mount_point=$(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.disk.space[$mount_point_id].point")
                            echo "       - $mount_point_name\-$mount_point"
                            (
                                umc df collect 15 5760 $mount_point |
                                    $umc_bin/csv2obd --resource disk:space\-$mount_point_name |
                                    $umc_bin/logdirector.pl -dir /var/log/umc -addDateSubDir -name disk:space\-$mount_point_name -detectHeader -checkHeaderDups -flush -tee |
                                    $umc_bin/dvdt --resource disk:space\-$mount_point_name | 
                                    $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name disk:space\-$mount_point_name\_dt -detectHeader -checkHeaderDups -flush
                            ) &
                            echo $! >>$umc_run/$svc_name.pid
                        done
                        ;;
                    network:if)
                        for key in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[]"); do
                            echo "       - $key"
                            (
                                umc ifconfig collect 5 2147483647 $key | 
                                    $umc_bin/csv2obd --resource network:if\-$key | 
                                    $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name network:if\-$key -detectHeader -checkHeaderDups -flush -tee |
                                    $umc_bin/dvdt --resource network:if\-$key | 
                                    $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name network:if\-$key\_dt -detectHeader -checkHeaderDups -flush
                            ) &
                            echo $! >>$umc_run/$svc_name.pid
                        done 
                        ;;
                    network:tcp)
                        for key in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem.$component[]"); do
                            echo "       - $key"
                            if [ $key == "stats" ]; then
                                (
                                    umc netstattcp collect 5 2147483647 | 
                                        $umc_bin/csv2obd --resource network:tcp:netstattcp | 
                                        $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name network:tcp:netstattcp -detectHeader -checkHeaderDups -flush -tee |
                                        $umc_bin/dvdt --resource network:tcp:netstattcp  | 
                                        $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name network:tcp:netstattcp\_dt -detectHeader -checkHeaderDups -flush
                                ) &
                                echo $! >>$umc_run/$svc_name.pid         
                            fi       
                        done      
                        ;;
                    esac
            done
        else
            for component in $(cat $umc_cfg/$umc_svc_def | y2j | jq -r ".$system[].os.$subsystem[]"); do
                
                echo "  - $subsystem\-$component"
                case $subsystem\-$component in
                system:vmstat)
                    (
                        umc vmstat collect 5 2147483647 | 
                            $umc_bin/csv2obd --resource $subsystem\-$component | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component -detectHeader -checkHeaderDups -flush
                    ) &
                    echo $! >>$umc_run/$svc_name.pid     
                    ;;
                system:uptime)
                    (
                        umc uptime collect 5 2147483647 | 
                            $umc_bin/csv2obd --resource $subsystem\-$component | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component -detectHeader -checkHeaderDups -flush
                    ) &
                    echo $! >>$umc_run/$svc_name.pid                        
                    ;;
                memory:meminfo)
                     (
                        umc meminfo collect 5 2147483647 | 
                            $umc_bin/csv2obd --resource $subsystem\-$component | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component -detectHeader -checkHeaderDups -flush -tee |
                            $umc_bin/dvdt --resource $subsystem\-$component  | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component\_dt -detectHeader -checkHeaderDups -flush
                    ) &                   
                    ;;
                memory:free)
                    (
                        umc free collect 5 2147483647 | 
                            $umc_bin/csv2obd --resource $subsystem\-$component | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component -detectHeader -checkHeaderDups -flush -tee |
                            $umc_bin/dvdt --resource $subsystem\-$component  | 
                            $umc_bin/logdirector.pl -addDateSubDir -dir /var/log/umc -name $subsystem\-$component\_dt -detectHeader -checkHeaderDups -flush
                    ) &
                    ;;
                esac
            done
        fi
    done
done


}

function stop() {
    if [ -f $umc_run/$svc_name.pid ]; then
        for tmp_umc_pid in $(cat $umc_run/$svc_name.pid); do
            sudo $umc_bin/killtree.sh $tmp_umc_pid
        done
        rm $umc_run/$svc_name.pid
    fi
}


function register_inetd() {
    cat >/tmp/umc_$service_type\-$svc_name <<EOF
#!/bin/bash
$umc_home/lib/$service_type.sh $svc_name.yml \$1
EOF

chmod +x /tmp/umc_$service_type\-$svc_name 
sudo mv /tmp/umc_$service_type\-$svc_name /etc/init.d/umc_$service_type\-$svc_name

sudo chkconfig --add umc_$service_type\-$svc_name 
sudo chkconfig --level 2345 umc_$service_type\-$svc_name on 

    echo echo "Service registered. Start the service:"
    cat <<EOF
sudo service umc_$service_type\-$svc_name start
sudo service umc_$service_type\-$svc_name status
sudo service umc_$service_type\-$svc_name stop
EOF
}

function register_systemd() {

    sudo cat >/etc/systemd/system/umc_$service_type\-$svc_name.service <<EOF
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
    sudo systemctl enable umc_$service_type\-$svc_name.service

    echo "Service registered. Start the service:"
    cat <<EOF
sudo systemctl restart umc_$service_type\-$svc_name.service
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


