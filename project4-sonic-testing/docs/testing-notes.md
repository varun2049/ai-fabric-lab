# Testing Notes - Project 4

## What this shows
The Project 3 SONiC fabric validated with SONiC's own three test frameworks, each at a
different layer:

| Framework | Layer | Method | Written here |
|---|---|---|---|
| DVS tests (`sonic-swss/tests`) | control plane | write CONFIG_DB, assert ASIC_DB | 2 tests |
| PTF | data plane | inject packets on ports, assert what is forwarded where | 2 tests |
| SPyTest | end to end | drive the switch over SSH through the framework's APIs, verify with parsed `show` output | 1 test |

All three run against `docker-sonic-vs` (community 202411) on one machine, alongside
the upstream suites they extend.

## DVS tests - control plane
A DVS test is the Project 3 trace as code: create a row in CONFIG_DB or APPL_DB, wait
for orchagent, assert the SAI object in ASIC_DB. The harness boots its own switch
container per file and builds the 32 backing interfaces itself.

Upstream suites run unchanged against this image:

| File | Covers | Result |
|---|---|---|
| test_vlan.py | VLAN objects | pass |
| test_vxlan_tunnel.py | tunnel termination | 3/3 |
| test_evpn_tunnel.py | P2P/P2MP tunnels, VLAN-VNI maps | 5/5 |
| test_evpn_fdb.py | remote MACs as FDB entries | 1/1 |
| test_evpn_l3_vxlan.py | VRF-VNI maps, L3VNI routes | 6/6 |

`tests/test_vni_map_direction.py` adds two tests derived from reading
`orchagent/vxlanorch.cpp`, asserting behaviour the upstream suite does not check:

- an L2 VNI produces exactly one tunnel-map entry, in the decapsulation direction
  (`VNI_TO_VLAN_ID`) - no encapsulation entry;
- binding a VRF to that VNI removes the VLAN entry and creates a
  `VNI_TO_VIRTUAL_ROUTER_ID` entry in its place.

```
types = map_types_for_vni(dvs, "1000")
assert "SAI_TUNNEL_MAP_TYPE_VNI_TO_VLAN_ID" not in types
assert "SAI_TUNNEL_MAP_TYPE_VNI_TO_VIRTUAL_ROUTER_ID" in types
```

Both pass. The harness is run from `runner/`, an image built from the switch image so
the host-side `swsscommon` bindings match the switch exactly.

## PTF - data plane
PTF binds to a set of ports, sends crafted packets, and asserts arrivals. The sink
container of the Project 3 lab terminates 28 of leaf1's ports in one namespace, so a
PTF container attached to that namespace has a real switch on the other end:
port 0 = Ethernet16 (Vlan100), port 1 = Ethernet20 (Vlan100), port 2 = Ethernet24
(Vlan110, VrfA). `prepare-dut.sh` adds these three ports to leaf1's configuration; the
Project 3 fabric is otherwise unchanged.

`ptf/tests/test_leaf1_forwarding.py`:

- **L2ForwardInVlan** - a MAC is learned from port 1; a frame to it from port 0 is
  delivered unchanged on port 1 and not on port 2.
- **RouteBetweenVlansInVrf** - resolves the gateway MAC by ARP as a host would, sends a
  packet for the Vlan110 subnet, answers the switch's own ARP for the destination on
  port 2, then asserts the forwarded packet byte for byte:

```
expected = simple_udp_packet(eth_dst=MAC2, eth_src=gw_mac, ip_src=H100, ip_dst=H110, ip_ttl=63)
verify_packet(self, expected, P2)
```

TTL decremented, source MAC rewritten to the gateway's, delivered only on the Vlan110
port. Both pass.

## SPyTest - end to end
SPyTest connects to the switch over SSH, configures it through API modules, and
verifies with `show` output parsed by TextFSM templates. `spytest/tests/test_leaf1_vlan.py`
creates VLAN 300, adds Ethernet28 untagged, verifies through `apis.switching.vlan`,
removes both and verifies the removal.

```
2026-09-06 19:50:59 Report(Pass): test_vlan_create_member_verify_delete: Test case passed
Results : [('Pass', 1)]
```

Running the framework against community SONiC took four decisions, each recorded
where it applies: the runner follows SPyTest's own container recipe (Ubuntu 20.04,
Python 3.8, its curated requirements, `spytest/Dockerfile`); the switch is a
`DevSonic` device over SSH with `config: empty` so the framework does not reload base
configuration on a single-container image (`testbed_leaf1.yaml`); `--feature-group
master` selects the community feature set, whose readiness check uses `show interfaces
status` rather than Broadcom-only status commands (`run-spytest.sh`); and two small
fixes to the public tree - a helper the VLAN API imports but the tree never defines,
and an index entry that shadowed the `show vlan config` template - are carried as
`upstream-fixes.patch`.

## Reproduce
```
# DVS (needs ~/src/sonic-swss, branch 202411)
cd runner && ./run-dvs.sh -v test_evpn_fdb.py && ./run-dvs.sh -v local/test_vni_map_direction.py

# PTF (needs the Project 3 fabric up, with the sink-facing ports in leaf1's config)
cd ptf && ./prepare-dut.sh && ./run-ptf.sh test_leaf1_forwarding.L2ForwardInVlan
        ./run-ptf.sh test_leaf1_forwarding.RouteBetweenVlansInVrf

# SPyTest (needs ~/src/sonic-mgmt with spytest checked out)
cd spytest && ./apply-upstream-fixes.sh && ./dut-enable-ssh.sh clab-p3-sonic-leaf1
./run-spytest.sh local/test_leaf1_vlan.py
```
