#!/usr/bin/env bash
# Apply the two local fixes this project needs in the public SPyTest tree:
#  - utilities/utils.py: define get_random_space_string (imported by apis/switching/vlan.py, never published)
#  - templates/index:    move 'show vlan config' above the 'show (v|V)lan.*' catch-all that shadows it
cd ~/src/sonic-mgmt && git apply --check "$(dirname "$0")/upstream-fixes.patch" 2>/dev/null && git apply "$(dirname "$0")/upstream-fixes.patch" && echo "applied" || echo "already applied or tree differs"
