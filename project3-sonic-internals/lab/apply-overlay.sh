#!/usr/bin/env bash
set -euo pipefail
LAB=clab-p3-sonic
for L in "$@"; do
  docker cp configs/$L/overlay.json $LAB-$L:/etc/sonic/$L-overlay.json
  docker exec $LAB-$L config load -y /etc/sonic/$L-overlay.json 2>/dev/null
  docker cp configs/$L/bgpd.conf $LAB-$L:/etc/frr/bgpd.conf
  docker exec $LAB-$L supervisorctl restart bgpd
done
