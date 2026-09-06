#!/usr/bin/env bash
# usage: ./run-ptf.sh <module.TestClass>
# ports: 0=sink eth1 (leaf1 Ethernet16, Vlan100)  1=eth2 (Ethernet20, Vlan100)  2=eth3 (Ethernet24, Vlan110)
exec docker run --rm --privileged --net=container:clab-p3-sonic-sink \
  -v "$(pwd)/tests:/ptf" ptf-runner --test-dir /ptf \
  --interface 0@eth1 --interface 1@eth2 --interface 2@eth3 "$@"
