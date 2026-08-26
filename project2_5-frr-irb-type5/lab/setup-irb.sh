#!/usr/bin/env bash
# Project 2.5 - symmetric IRB: VRFs, anycast gateways, L2VNIs, L3VNIs
set -euo pipefail
LAB=clab-p25-irb
ANYCAST_MAC=00:00:5e:00:01:01

vrf()   { docker exec $LAB-$1 ip link add $2 type vrf table $3
          docker exec $LAB-$1 ip link set $2 up; }

# l2vni NODE VNI VTEP PORT GW_CIDR VRF   (PORT="-" for stretched subnet, no host)
l2vni() { local N=$1 V=$2 T=$3 P=$4 GW=$5 VR=$6
  docker exec $LAB-$N ip link add br$V type bridge
  docker exec $LAB-$N ip link add vxlan$V type vxlan id $V local $T dstport 4789 nolearning
  docker exec $LAB-$N ip link set vxlan$V master br$V
  [ "$P" != "-" ] && docker exec $LAB-$N ip link set $P master br$V
  docker exec $LAB-$N bridge link set dev vxlan$V learning off neigh_suppress on
  docker exec $LAB-$N ip link set br$V master $VR              # SVI joins the tenant VRF
  docker exec $LAB-$N ip link set br$V address $ANYCAST_MAC    # anycast gateway MAC
  docker exec $LAB-$N ip addr add $GW dev br$V                 # anycast gateway IP
  docker exec $LAB-$N ip link set br$V up
  docker exec $LAB-$N ip link set vxlan$V up
  [ "$P" != "-" ] && docker exec $LAB-$N ip link set $P up || true; }

# l3vni NODE VNI VTEP VRF RMAC - hostless routing highway; RMAC on both devices
l3vni() { local N=$1 V=$2 T=$3 VR=$4 R=$5
  docker exec $LAB-$N ip link add br$V type bridge
  docker exec $LAB-$N ip link add vxlan$V type vxlan id $V local $T dstport 4789 nolearning
  docker exec $LAB-$N ip link set vxlan$V master br$V
  docker exec $LAB-$N bridge link set dev vxlan$V learning off
  docker exec $LAB-$N ip link set br$V master $VR
  docker exec $LAB-$N ip link set br$V address $R
  docker exec $LAB-$N ip link set vxlan$V address $R
  docker exec $LAB-$N ip link set br$V up
  docker exec $LAB-$N ip link set vxlan$V up; }

for N in leaf1 leaf2; do
  vrf $N tenantA 1001
  vrf $N tenantB 1002
  docker exec $LAB-$N touch /etc/frr/vtysh.conf
done

# leaf1: subnets 100 (h1) + 200 (h3); leaf2: 100 stretched (anycast, no host), 101 (h2), 201 (h4)
l2vni leaf1 100 10.255.0.11 eth2 192.168.100.1/24 tenantA
l2vni leaf1 200 10.255.0.11 eth4 192.168.200.1/24 tenantB
l2vni leaf2 100 10.255.0.12 -    192.168.100.1/24 tenantA
l2vni leaf2 101 10.255.0.12 eth2 192.168.101.1/24 tenantA
l2vni leaf2 201 10.255.0.12 eth4 192.168.201.1/24 tenantB

l3vni leaf1 1000 10.255.0.11 tenantA aa:bb:cc:00:00:11
l3vni leaf1 2000 10.255.0.11 tenantB aa:bb:cc:00:00:11
l3vni leaf2 1000 10.255.0.12 tenantA aa:bb:cc:00:00:12
l3vni leaf2 2000 10.255.0.12 tenantB aa:bb:cc:00:00:12

echo "== verify =="
docker exec $LAB-leaf1 vtysh -c "show evpn vni"
