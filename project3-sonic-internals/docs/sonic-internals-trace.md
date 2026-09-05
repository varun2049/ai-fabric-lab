# SONiC Internals Trace - Project 3

## What this shows
Three pieces of network state followed through every layer of SONiC on a live two-leaf
fabric: a BGP route from the underlay, a remote MAC learned through EVPN, and a VNI
mapping. At each layer the state is read verbatim - FRR, the kernel, APPL_DB, ASIC_DB,
and the SAI recording - so the same object is visible in every place it exists. The
SONiC design expects these copies to be consistent; a debugging session is finding the
first layer where they are not. The last section reads the orchagent code that produced
the recorded SAI calls.

## Lab
Two SONiC leaves (docker-sonic-vs, 202411 build; each with 32 backed data interfaces),
two FRR spines, four hosts. Underlay: eBGP, leaf ASNs 65011/65012, spines 65100,
leaf loopbacks 10.255.0.11/.12 (the VTEPs). Overlay: VNI 100 mapped to Vlan100 on both
leaves, h1 attached on leaf1 Ethernet4, leaf2 hostless. Configuration by CONFIG_DB
tables (`config load`) plus FRR `bgpd.conf` with `advertise-all-vni`.

## Trace 1 - a BGP route in four places
Prefix: leaf2's loopback 10.255.0.12/32, seen from leaf1.

**1. bgpd - the decision**
```
vtysh -c "show ip bgp 10.255.0.12/32"
Paths: (2 available, best #2, table default)
  65100 65012
      Origin IGP, valid, external, multipath
  65100 65012
      Origin IGP, valid, external, multipath, best (Router ID)
```
Two paths with identical AS_PATHs - both spines share ASN 65100 - so both are
`multipath`. The Project 1 ECMP design, unchanged under SONiC.

**2. Kernel FIB - zebra's installation over netlink**
```
ip route show 10.255.0.12
10.255.0.12 proto bgp metric 20
        nexthop via 10.0.1.0 dev Ethernet0 weight 1
        nexthop via 10.0.11.0 dev Ethernet8 weight 1
```

**3. APPL_DB - zebra's second copy, via FPM to fpmsyncd**
```
redis-cli -n 0 hgetall 'ROUTE_TABLE:10.255.0.12'
protocol  bgp
nexthop   10.0.1.0,10.0.11.0
ifname    Ethernet0,Ethernet8
weight    1,1
```
Same two next-hops, encoded as lists for routeorch. SONiC drops `/32` from host-route
keys.

**4. ASIC_DB - routeorch's SAI object**
```
ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"10.255.0.12/32","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000022"}
```
Routes are a SAI *entry* type: keyed by virtual router and prefix rather than by an
object ID. `vr` is the default VIRTUAL_ROUTER object.

**Data plane**
```
ping -c 2 -I 10.255.0.11 10.255.0.12
64 bytes from 10.255.0.12: icmp_seq=1 ttl=63 time=0.501 ms
```
ttl=63: one routed hop through a spine.

## Trace 2 - a remote MAC in five places
Object: h1's MAC `aa:c1:ab:1d:4d:b9`, attached to leaf1, seen from leaf2 - which has no
host in the VLAN and learned it only through EVPN.

**1. FRR - the Type-2 route imported**
```
vtysh -c "show evpn mac vni 100"
MAC               Type   Flags Intf/Remote ES/VTEP            VLAN  Seq #'s
aa:c1:ab:1d:4d:b9 remote       10.255.0.11                          0/0
```

**2. Kernel FDB - zebra installs it, flagged extern_learn**
```
bridge fdb show | grep aa:c1:ab:1d:4d:b9
aa:c1:ab:1d:4d:b9 dev vtep1-100 vlan 100 extern_learn master Bridge
aa:c1:ab:1d:4d:b9 dev vtep1-100 dst 10.255.0.11 self extern_learn
```
Two entries, as in Project 2: the bridge's egress port, and the VXLAN device's
remote-VTEP mapping. `extern_learn` marks them controller-installed and never aged.

**3. APPL_DB - fdbsyncd mirrors the kernel event**
```
redis-cli -n 0 keys 'VXLAN_*'
VXLAN_TUNNEL_TABLE:vtep1
VXLAN_REMOTE_VNI_TABLE:Vlan100:10.255.0.11
VXLAN_FDB_TABLE:Vlan100:aa:c1:ab:1d:4d:b9
```
The remote-VNI row is the imported Type-3 (leaf1 participates in VNI 100); the FDB
row is the imported Type-2.

**4. ASIC_DB - fdborch writes the FDB entry**
```
ASIC_STATE:SAI_OBJECT_TYPE_FDB_ENTRY:{"bvid":"oid:0x2600000000061e","mac":"AA:C1:AB:1D:4D:B9","switch_id":"oid:0x21000000000000"}
```
`bvid` is the Vlan100 bridge object. Two tunnel objects and one tunnel-map entry
exist alongside it.

**5. The recording - the SAI call syncd executed**
```
grep -i 1D:4D:B9 /var/log/swss/sairedis.rec | grep '|c|'
2026-09-04.23:18:28.363635|c|SAI_OBJECT_TYPE_FDB_ENTRY:{"bvid":"oid:0x2600000000061e","mac":"AA:C1:AB:1D:4D:B9","switch_id":"oid:0x21000000000000"}|SAI_FDB_ENTRY_ATTR_TYPE=SAI_FDB_ENTRY_TYPE_STATIC|SAI_FDB_ENTRY_ATTR_ALLOW_MAC_MOVE=true|SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID=oid:0x3a000000000627|SAI_FDB_ENTRY_ATTR_ENDPOINT_IP=10.255.0.11
```
Read field by field: a create (`c`); the entry keyed by bridge-VLAN and MAC;
`TYPE=STATIC` - EVPN-learned MACs are installed static, the chip's equivalent of the
kernel's `extern_learn`; `ALLOW_MAC_MOVE=true` - mobility permitted; `BRIDGE_PORT_ID`
- the tunnel's bridge port, not a physical port; `ENDPOINT_IP=10.255.0.11` - the
remote VTEP, the chip's equivalent of the kernel entry's `dst`. On hardware this line
is what the SAI library turns into a chip table write; if the write fails, this file
is the evidence that goes to the silicon vendor.

**Data plane**
```
ping (h1) -c 3 192.168.100.2        # an SVI on leaf2, across the tunnel
64 bytes from 192.168.100.2: icmp_seq=1 ttl=64 time=2.46 ms
3 packets transmitted, 3 received, 0% packet loss
```
ttl=64: bridged, not routed - the Project 2 proof, now through SONiC's pipeline.

## Trace 3 - a VNI map in five places
Object: the mapping `VNI 100 ↔ Vlan100` on leaf1.

```
# 1. CONFIG_DB - the row
redis-cli -n 4 hgetall 'VXLAN_TUNNEL_MAP|vtep1|map_100_Vlan100'
vlan Vlan100   vni 100

# 2. Kernel - vxlanmgrd's netdev (the Project 2 command, typed by a daemon)
ip -d link show vtep1-100
44: vtep1-100: ... master Bridge
    vxlan id 100 local 10.255.0.11 srcport 0 0 dstport 4789 nolearning ...

# 3. APPL_DB - vxlanmgrd's published row
VXLAN_TUNNEL_MAP_TABLE:vtep1:map_100_Vlan100   vlan Vlan100   vni 100

# 4. ASIC_DB - vxlanorch's SAI object
ASIC_STATE:SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY:oid:0x3b000000000630
SAI_TUNNEL_MAP_ENTRY_ATTR_TUNNEL_MAP_TYPE   SAI_TUNNEL_MAP_TYPE_VNI_TO_VLAN_ID
SAI_TUNNEL_MAP_ENTRY_ATTR_TUNNEL_MAP        oid:0x29000000000618
SAI_TUNNEL_MAP_ENTRY_ATTR_VLAN_ID_VALUE     100
SAI_TUNNEL_MAP_ENTRY_ATTR_VNI_ID_KEY        100

# 5. The recording
2026-09-05.00:06:29.491584|c|SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY:oid:0x3b000000000630|...VNI_TO_VLAN_ID|...|SAI_TUNNEL_MAP_ENTRY_ATTR_VLAN_ID_VALUE=100|SAI_TUNNEL_MAP_ENTRY_ATTR_VNI_ID_KEY=100
```

One L2 VNI produces one map entry, in the decapsulation direction (VNI key to VLAN
value). The L3VNI is different - the line above it in the same recording:

```
|c|SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY:oid:0x3b00000000061f|...VNI_TO_VIRTUAL_ROUTER_ID|...|SAI_TUNNEL_MAP_ENTRY_ATTR_VIRTUAL_ROUTER_ID_VALUE=oid:0x3000000000615|SAI_TUNNEL_MAP_ENTRY_ATTR_VNI_ID_KEY=1000
```

VNI 1000 maps to a virtual router, not a VLAN: packets arriving with that VNI are routed
in VrfA. That is the L3VNI as the chip sees it.

## The reverse - a deliberate removal
`config vxlan map del vtep1 100 100` on leaf1, then each layer re-read:

```
CONFIG_DB  keys '*map_100_*'            (none)
APPL_DB    keys '*map_100_*'            (none)
kernel     ip link show vtep1-100       Device "vtep1-100" does not exist.
ASIC_DB    map entries with VNI 100     (none)
recording  2026-09-05.03:09:57|r|SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY:oid:0x3b000000000630
leaf2      show evpn vni 100            no remote VTEPs
```

The same object ID created in Trace 3 is removed (`r`), and leaf2 loses leaf1 because
leaf1's Type-3 for VNI 100 is withdrawn. `config vxlan map add vtep1 100 100` restored
every layer. The pipeline runs both ways, and the first layer that still holds a
removed object names the daemon that failed to clean up.

## What the code did (sonic-swss, branch 202411)
The functions behind the recording lines above.

**`VxlanTunnelMapOrch::addOperation` (vxlanorch.cpp ~1960-1998)** - handles a
`VXLAN_TUNNEL_MAP` row. It takes the tunnel's *decap* map and asks
`vrf_orch->isL3VniVlan(vni_id)`:

```
if (isL3Vni == false)
    tunnel_map_entry_id = create_tunnel_map_entry(MAP_T::VNI_TO_VLAN_ID, tunnel_map_id, vni_id, vlan_id);
else
    ... map_entry_id = SAI_NULL_OBJECT_ID;
```

An L2 VNI gets exactly one entry, decap direction - which is what Trace 3 found. A VLAN
that serves an L3VNI gets none here; the VRF path owns it. (A second function,
`VxlanTunnelOrch::createVxlanTunnelMap`, creates encap and decap entries together -
that is the static/VNET tunnel path, not the EVPN one.)

**`VxlanVrfMapOrch::addOperation` (vxlanorch.cpp ~2208-2230)** - handles the
`VRF ... vni` row. If a VLAN map entry exists for that VNI it removes it, then creates
both directions between VNI and virtual router:

```
entry.encap_id = tunnel_obj->addEncapMapperEntry(vrf_id, vni_id);
entry.decap_id = tunnel_obj->addDecapMapperEntry(vrf_id, vni_id);
```

The decap entry is the `VNI_TO_VIRTUAL_ROUTER_ID` line in the recording.

**`FdbOrch::addFdbEntry` (fdborch.cpp ~1370-1445)** - the four attributes of the
Trace 2 recording line, each to its condition:

```
if (fdbData.origin == FDB_ORIGIN_VXLAN_ADVERTIZED)
    attr.value.s32 = SAI_FDB_ENTRY_TYPE_STATIC;                 // TYPE=STATIC
if ((origin == FDB_ORIGIN_VXLAN_ADVERTIZED || MCLAG) && fdbData.type == "dynamic")
    attr.id = SAI_FDB_ENTRY_ATTR_ALLOW_MAC_MOVE; attr.value.booldata = true;   // ALLOW_MAC_MOVE=true
attr.id = SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID; attr.value.oid = port.m_bridge_port_id;   // the tunnel's bridge port
if (fdbData.origin == FDB_ORIGIN_VXLAN_ADVERTIZED)
    attr.id = SAI_FDB_ENTRY_ATTR_ENDPOINT_IP; ... = fdbData.remote_ip;        // ENDPOINT_IP=10.255.0.11
```

`origin` is set by fdbsyncd when it writes `VXLAN_FDB_TABLE` from the kernel event zebra
caused. An EVPN-learned MAC is therefore always installed static with an endpoint IP -
the chip-side reason `show mac`'s physical-port view omits it.

## What was proven
1 A route selected by bgpd exists in the kernel, APPL_DB, and ASIC_DB with the same
two ECMP next-hops - the four copies SONiC's design requires to agree.
2 A MAC learned by EVPN on one leaf becomes a static FDB entry in the other leaf's
ASIC_DB, pointing at a tunnel bridge port and the remote VTEP, with the exact SAI call
recorded and timestamped.
3 Both were located by reading each layer's table directly; no layer had to be
inferred.
4 A configuration row's SAI object is created and removed by identifiable functions in
orchagent; the recording shows the same object ID at both ends of its life.

## Scope
Observed on the virtual platform, not defects in the pipeline: `show mac` lists only
MACs on physical ports and omits tunnel entries that ASIC_DB holds; the EVPN tunnel
reports `operstatus down` in STATE_DB while forwarding works, because the virtual SAI
does not raise tunnel state notifications; and a leaf's own `eth2` endpoint MAC leaks
into the VLAN as a learned MAC. Hardware enforcement of anything below the SAI call
(buffers, QoS, line-rate forwarding) is outside what this platform can show.

## Commands used
```
docker exec clab-p3-sonic-leaf1 vtysh -c "show ip bgp 10.255.0.12/32"
docker exec clab-p3-sonic-leaf1 ip route show 10.255.0.12
docker exec clab-p3-sonic-leaf1 redis-cli -n 0 hgetall 'ROUTE_TABLE:10.255.0.12'
docker exec clab-p3-sonic-leaf1 redis-cli -n 1 keys '*ROUTE_ENTRY*'
docker exec clab-p3-sonic-leaf2 vtysh -c "show evpn mac vni 100"
docker exec clab-p3-sonic-leaf2 bridge fdb show
docker exec clab-p3-sonic-leaf2 redis-cli -n 0 keys 'VXLAN_*'
docker exec clab-p3-sonic-leaf2 redis-cli -n 1 keys '*FDB_ENTRY*'
docker exec clab-p3-sonic-leaf2 grep -i 1D:4D:B9 /var/log/swss/sairedis.rec
docker exec clab-p3-sonic-leaf1 redis-cli -n 4 hgetall 'VXLAN_TUNNEL_MAP|vtep1|map_100_Vlan100'
docker exec clab-p3-sonic-leaf1 ip -d link show vtep1-100
docker exec clab-p3-sonic-leaf1 redis-cli -n 1 hgetall 'ASIC_STATE:SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY:oid:0x3b000000000630'
docker exec clab-p3-sonic-leaf1 config vxlan map del vtep1 100 100
docker exec clab-p3-sonic-leaf1 config vxlan map add vtep1 100 100
git clone --depth 1 -b 202411 https://github.com/sonic-net/sonic-swss.git
```
