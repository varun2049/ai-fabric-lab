#!/usr/bin/env bash
# Project 3 - SONiC leaves: load CONFIG_DB, start bgpd with FRR config
set -euo pipefail
LAB=clab-p3-sonic

wait_ports() {   # SONiC ports must all initialize before it accepts most config
  for i in $(seq 1 48); do
    n=$(docker exec $LAB-$1 redis-cli -n 1 keys "*HOSTIF:*" 2>/dev/null | wc -l | tr -d " ")
    [ "$n" -ge 32 ] && { echo "$1: $n host interfaces, ports ready"; return; }
    sleep 5
  done
  echo "$1: ports never became ready"; exit 1
}

leaf() {
  wait_ports $1
  docker cp configs/$1/config.json $LAB-$1:/etc/sonic/$1.json
  docker exec $LAB-$1 config load -y /etc/sonic/$1.json 2>/dev/null
  docker cp configs/$1/bgpd.conf $LAB-$1:/etc/frr/bgpd.conf
  docker exec $LAB-$1 supervisorctl start bgpd
}

for L in "$@"; do leaf $L; done
