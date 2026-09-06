#!/usr/bin/env bash
# Add the three sink-facing test ports to leaf1 (Ethernet16/20 in Vlan100, Ethernet24 in
# Vlan110/VrfA). 'config load' merges, so the Project 3 fabric is otherwise untouched.
C=${1:-clab-p3-sonic-leaf1}
docker cp "$(dirname "$0")/leaf1-ptf-ports.json" $C:/etc/sonic/ptf-ports.json
docker exec $C config load -y /etc/sonic/ptf-ports.json 2>/dev/null && echo "PTF ports loaded on $C"
