#!/usr/bin/env bash
# Project 2 Part A - raw VXLAN, no control plane
# Run after: sudo containerlab deploy -t topology.clab.yml
set -euo pipefail

LAB=clab-p2-static

setup_leaf () {
  local NODE=$1 VTEP=$2 REMOTE=$3
  echo "== ${NODE}: VTEP ${VTEP}, flood target ${REMOTE} =="
  docker exec ${LAB}-${NODE} ip link add br100 type bridge
  docker exec ${LAB}-${NODE} ip link add vxlan100 type vxlan id 100 \
      local ${VTEP} dstport 4789 nolearning
  docker exec ${LAB}-${NODE} ip link set vxlan100 master br100
  docker exec ${LAB}-${NODE} ip link set eth2 master br100
  docker exec ${LAB}-${NODE} ip link set br100 up
  docker exec ${LAB}-${NODE} ip link set vxlan100 up
  docker exec ${LAB}-${NODE} ip link set eth2 up
  # THE defining line of Part A: a human tells the VTEP where to flood.
  # In Part B (evpn/) this entry is installed by BGP from a Type-3 route instead.
  docker exec ${LAB}-${NODE} bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst ${REMOTE}
  docker exec ${LAB}-${NODE} touch /etc/frr/vtysh.conf
}

setup_leaf leaf1 10.255.0.11 10.255.0.12
setup_leaf leaf2 10.255.0.12 10.255.0.11

echo "== verify =="
docker exec ${LAB}-leaf1 bridge fdb show dev vxlan100
echo "expect: the static all-zeros entry pointing at 10.255.0.12"
