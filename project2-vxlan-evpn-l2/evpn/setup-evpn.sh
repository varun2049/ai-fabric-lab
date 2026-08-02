#!/usr/bin/env bash
# Project 2 Part B - EVPN overlay, two tenants
# Run after: sudo containerlab deploy -t topology.clab.yml
# containerlab does not persist kernel interfaces, so this rebuilds them.
set -euo pipefail

LAB=clab-p2-evpn

# one L2VNI: its own bridge, its own vxlan device, its own host port.
# separate bridges are the first isolation mechanism - a frame in br100
# has no path into br200.
setup_vni () {
  local NODE=$1 VTEP=$2 VNI=$3 PORT=$4 SVI=$5
  echo "== ${NODE}: VNI ${VNI} on ${PORT}, VTEP ${VTEP}, SVI ${SVI} =="
  docker exec ${LAB}-${NODE} ip link add br${VNI} type bridge
  docker exec ${LAB}-${NODE} ip link add vxlan${VNI} type vxlan id ${VNI} \
      local ${VTEP} dstport 4789 nolearning
  docker exec ${LAB}-${NODE} ip link set vxlan${VNI} master br${VNI}
  docker exec ${LAB}-${NODE} ip link set ${PORT} master br${VNI}
  # EVPN populates the tables, so kill data-plane learning and enable ARP suppression
  docker exec ${LAB}-${NODE} bridge link set dev vxlan${VNI} learning off neigh_suppress on
  # SVI: gives the leaf an L3 presence so it holds IP-to-MAC bindings.
  # Without this, Type-2 routes are MAC-only and ARP suppression cannot work.
  docker exec ${LAB}-${NODE} ip addr add ${SVI}/24 dev br${VNI}
  docker exec ${LAB}-${NODE} ip link set br${VNI} up
  docker exec ${LAB}-${NODE} ip link set vxlan${VNI} up
  docker exec ${LAB}-${NODE} ip link set ${PORT} up
}

# tenant A - VNI 100, 192.168.100.0/24, hosts h1/h2 on eth2
setup_vni leaf1 10.255.0.11 100 eth2 192.168.100.1
setup_vni leaf2 10.255.0.12 100 eth2 192.168.100.2

# tenant B - VNI 200, 192.168.200.0/24, hosts h3/h4 on eth4
# note: same host addresses (.10/.20) as tenant A on purpose - overlapping
# tenant address space is normal, and it makes the isolation test unambiguous.
setup_vni leaf1 10.255.0.11 200 eth4 192.168.200.1
setup_vni leaf2 10.255.0.12 200 eth4 192.168.200.2

for N in leaf1 leaf2; do
  docker exec ${LAB}-${N} touch /etc/frr/vtysh.conf
done

echo "== populating neighbour tables (leaf ARPs for its local hosts) =="
docker exec ${LAB}-leaf1 ping -c 2 -I br100 192.168.100.10 >/dev/null || true
docker exec ${LAB}-leaf2 ping -c 2 -I br100 192.168.100.20 >/dev/null || true
docker exec ${LAB}-leaf1 ping -c 2 -I br200 192.168.200.10 >/dev/null || true
docker exec ${LAB}-leaf2 ping -c 2 -I br200 192.168.200.20 >/dev/null || true

echo "== verify =="
docker exec ${LAB}-leaf1 vtysh -c "show evpn vni"
echo "expect: VNI 100 and VNI 200, each 2 MACs / 2 ARPs / 1 remote VTEP"
