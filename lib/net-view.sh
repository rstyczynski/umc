#!/bin/bash

function add_view() {
  view_name=$1

  unset service_added
  unset instance_added
  cat <<EOF
{
  "title": "$view_name"
EOF
  view_added=TRUE
}

function add_service() {
  local service_name=$1
  if [ "$service_added" == TRUE ]; then
    echo '],'
  else
    cat <<EOF
  ,
  "services": 
    {
EOF
  fi

  cat <<EOF
    "${service_name}": [
EOF
  service_added=TRUE
  instance_added=FALSE
}

function close_service() {
  echo ']'
  echo '}'
}

function close_view() {
  echo '}'
}

function add_icmp_instance() {
  local instance_name=$1
  local instance_label=$2
  local instance_mtr_csv=$3
  local instance_socket_csv=$4

  if [ "$instance_added" == TRUE ]; then
    echo ','
  fi

  cat <<EOF
        {
          "instance": "${instance_name}",
          "label": "${instance_label}",
          "layout": "view_1x2",
          "csv_file": "${instance_mtr_csv}",
          "views": [
            {
              "type": "mtr.avg"
            },
            {
              "type": "mtr.loss",
              "y_minmax": [0,100]
            },
            {
              "type": "mtr.hops"
            }
          ]
        }
EOF
  instance_added=TRUE
}

function add_tcp_instance() {
  local instance_name=$1
  local instance_label=$2
  local instance_mtr_csv=$3
  local instance_socket_csv=$4

  if [ "$instance_added" == TRUE ]; then
    echo ','
  fi

  cat <<EOF
        {
          "instance": "${instance_name}",
          "label": "${instance_label}",
          "layout": "view_2x4",
          "csv_file": "${instance_mtr_csv}",
          "views": [
            {
              "type": "mtr.avg"
            },
            {
              "type": "socket.tcp",
              "csv_file": "${instance_socket_csv}"
            },
            {
              "type": "mtr.loss",
              "y_minmax": [0,100]
            },
            {
              "type": "mtr.hops"
            },
            {
              "csv_file": "${instance_socket_csv}",
              "type": "socket.resolve"
            }
          ]
        }
EOF
  instance_added=TRUE
}

function build_test() {

  add_view "ILS network services"
  add_service ILS
  add_tcp_instance x1 x2 c3 x4
  add_tcp_instance y1 y2 y3 y4
  add_service DB
  add_tcp_instance z1 z2 z3 z4
  add_tcp_instance a1 a2 a3 a4
  add_service CPE
  add_icmp_instance z1 z2 z3 z4
  add_icmp_instance a1 a2 a3 a4
  close_service
  close_view

}


function build_DB_view() {
  local view_name=$1
  local service_name=DB
  
  
  add_view "${view_name}"
  add_service "${service_name}"

  for id in ${!url2name[@]}; do
    target_name=$(echo ${url2name[$id]} | tr ' ' '\n' | tail -1 | tr '\n-' _ | tr -d / | sed 's/_$//')
    add_tcp_instance ${target_name} ${target_name} mtr_${service_name}-${target_name}.log socket_${service_name}-${target_name}.log
  done
  close_service
  close_view
}
function build_JCA_view() {
  local view_name=$1
  add_view "${view_name}"

  for service_name in FTP MQ MQJMS; do

    add_service "${service_name}"

    case $service_name in

    FTP)
      for id in ${!jca2ftp[@]}; do
        target_name=$(echo ${jca2ftp[$id]} | tr ' ' '\n' | tail -1 | tr '\n-' _ | tr -d / | sed 's/_$//')
        add_tcp_instance ${target_name} ${target_name} mtr_${service_name}-${target_name}.log socket_${service_name}-${target_name}.log
      done
      ;;

      MQ)
      for id in ${!jca2mq[@]}; do
        target_name=$(echo ${jca2mq[$id]} | tr ' ' '\n' | tail -1 | tr '\n-' _ | tr -d / | sed 's/_$//')
        add_tcp_instance ${target_name} ${target_name} mtr_${service_name}-${target_name}.log socket_${service_name}-${target_name}.log
      done
      ;;

      MQJMS)
      for id in ${!jca2mqjms[@]}; do
        target_name=$(echo ${jca2mqjms[$id]} | tr ' ' '\n' | tail -1 | tr '\n-' _ | tr -d / | sed 's/_$//')
        add_tcp_instance ${target_name} ${target_name} mtr_${service_name}-${target_name}.log socket_${service_name}-${target_name}.log
      done

      ;;

    esac

  done
  close_service
  close_view
}

# DB view
# build_DB_view wls
# build_JCA_view jca
