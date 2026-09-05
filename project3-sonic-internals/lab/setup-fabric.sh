#!/usr/bin/env bash
# Project 3 - SONiC leaves: wait for ports, load CONFIG_DB, bind L3VNIs in zebra, start bgpd
set -euo pipefail
LAB=clab-p3-sonic

wait_ports() {
  for i in $(seq 1 48); do
    n=$(docker exec $LAB-$1 redis-cli -n 1 keys "*HOSTIF:*" 2>/dev/null | wc -l | tr -d ' ')
    [ "$n" -ge 32 ] && { echo "$1: ports ready"; return; }
    sleep 5
  done; echo "$1: ports never became ready"; exit 1
}

leaf() {
  wait_ports $1
  docker cp configs/$1/config_db.json $LAB-$1:/etc/sonic/$1.json
  docker exec $LAB-$1 config load -y /etc/sonic/$1.json 2>/dev/null
  sleep 10
  docker exec $LAB-$1 vtysh -c "conf t" -c "vrf VrfA" -c "vni 1000" -c "exit-vrf" -c "vrf VrfB" -c "vni 2000" -c "exit-vrf" 2>/dev/null
  docker cp configs/$1/bgpd.conf $LAB-$1:/etc/frr/bgpd.conf
  docker exec $LAB-$1 supervisorctl start bgpd
}

for L in leaf1 leaf2; do leaf $L; done
sleep 30
docker exec $LAB-leaf1 vtysh -c "show evpn vni" 2>/dev/null
echo "expect: VNIs 100/200 (L2) and 1000/2000 (L3) on leaf1"
