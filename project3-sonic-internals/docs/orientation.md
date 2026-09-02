# SONiC Orientation - Project 3

## What this shows
A live SONiC node (docker-sonic-vs, 202411 build) walked layer by layer: the daemons,
the Redis databases, and one configuration change followed from the CLI to the SAI call
that programs the switch. This is the pipeline the rest of the project traces.

## Lab
One `sonic-vs` node in containerlab with 32 data interfaces to a Linux node. The virtual
switch backs each front-panel port with a container interface (`eth1` = Ethernet0,
`eth2` = Ethernet4, +4 per interface, per `/usr/share/sonic/hwsku/lanemap.ini`):

```
eth1:25,26,27,28
eth2:29,30,31,32
```

## Daemons
`supervisorctl status` (excerpt). SONiC runs as supervised processes in this image; on
hardware the same daemons are split across containers.

```
fdbsyncd                         RUNNING   pid 154
fpmsyncd                         RUNNING   pid 160
intfmgrd                         RUNNING   pid 310
neighsyncd                       RUNNING   pid 151
orchagent                        RUNNING   pid 105
portsyncd                        RUNNING   pid 100
redis-server                     RUNNING   pid 51
syncd                            RUNNING   pid 80
vlanmgrd                         RUNNING   pid 316
vrfmgrd                          RUNNING   pid 166
vxlanmgrd                        RUNNING   pid 354
zebra                            RUNNING   pid 336
bgpd                             STOPPED   Not started
```

Four families: `*mgrd` managers consume CONFIG_DB and program the kernel and APPL_DB;
`*syncd` synchronizers mirror kernel netlink events into Redis; `orchagent` translates
APPL_DB into SAI objects in ASIC_DB; `syncd` executes ASIC_DB against the SAI library.
FRR (`zebra`, `bgpd`) runs alongside; `bgpd` starts once BGP is configured.

## Databases
From `/var/run/redis/sonic-db/database_config.json` on this node (id, key separator):

```
APPL_DB 0 :        ASIC_DB 1 :          COUNTERS_DB 2 :     CONFIG_DB 4 |
PFC_WD_DB 5 :      FLEX_COUNTER_DB 5 :  STATE_DB 6 |        SNMP_OVERLAY_DB 7 |
GB_ASIC_DB 9 :     GB_COUNTERS_DB 10 :  GB_FLEX_COUNTER_DB 11 :   APPL_STATE_DB 14 :
```

This build has no LOGLEVEL_DB and adds gearbox (`GB_*`) and APPL_STATE databases -
the ids are read from the node, not assumed. CONFIG_DB and STATE_DB key with `|`,
APPL_DB and ASIC_DB with `:`. One row from each of the four that matter most:

```
# CONFIG_DB - what the operator asked for
redis-cli -n 4 hgetall 'PORT|Ethernet64'
1) "alias"  2) "fortyGigE0/64"  3) "index"  4) "16"
5) "lanes"  6) "69,70,71,72"    7) "speed"  8) "100000"

# STATE_DB - what actually happened
redis-cli -n 6 hgetall 'PORT_TABLE|Ethernet0'
state ok · netdev_oper_status down · admin_status down · mtu 9100 · host_tx_ready true

# COUNTERS_DB - keyed by SAI object ID, via a name map
redis-cli -n 2 hget COUNTERS_PORT_NAME_MAP Ethernet0
oid:0x1000000000002
```

## One change, six hops
`config vlan add 100`, then each layer read in order.

```
# 1. CONFIG_DB
redis-cli -n 4 hgetall 'VLAN|Vlan100'
1) "vlanid"  2) "100"

# 2. Kernel - vlanmgrd added the VLAN to the single filtering bridge
ip link show Vlan100
36: Vlan100@Bridge: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc noqueue state UP

# 3. APPL_DB - vlanmgrd published the validated row
redis-cli -n 0 hgetall 'VLAN_TABLE:Vlan100'
1) "admin_status"  2) "up"   3) "mtu"  4) "9100"   5) "mac"  6) "02:42:ac:14:14:02"

# 4. ASIC_DB - orchagent wrote the SAI object
redis-cli -n 1 keys '*SAI_OBJECT_TYPE_VLAN:*'
1) "ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x26000000000051"   <- default VLAN, from boot
2) "ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x26000000000614"   <- VLAN 100
redis-cli -n 1 hgetall 'ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x26000000000614'
1) "SAI_VLAN_ATTR_VLAN_ID"  2) "100"

# 5-6. The recording - the SAI call syncd executed
grep '|c|SAI_OBJECT_TYPE_VLAN' /var/log/swss/sairedis.rec
2026-09-02.18:44:37.002583|c|SAI_OBJECT_TYPE_VLAN:oid:0x26000000000614|SAI_VLAN_ATTR_VLAN_ID=100
```

`c` is a create; response lines in the same file use uppercase. The object ID in the
recording is the one ASIC_DB holds. Every hop is a row that can be read, which is what
makes the pipeline debuggable by inspection: the first layer where a row is missing
names the daemon responsible for producing it.

## FRR
`/etc/frr/` holds `daemons`, `vtysh.conf`, `zebra.conf` - no BGP config yet, so bgpd
is not started. zebra's running config shows the link into the SONiC pipeline:

```
frr version 10.0.1
fpm address 127.0.0.1
no fpm use-next-hop-groups
```

`fpm address` is the channel over which zebra hands routes to `fpmsyncd`, which writes
them to APPL_DB for `routeorch` - the path a BGP route takes into the ASIC, alongside
its normal installation into the kernel.

## Commands used
```
docker exec clab-sonic-test-s1 supervisorctl status
docker exec clab-sonic-test-s1 redis-cli -n <db> keys '<pattern>'
docker exec clab-sonic-test-s1 redis-cli -n <db> hgetall '<key>'
docker exec clab-sonic-test-s1 config vlan add 100
docker exec clab-sonic-test-s1 ip link show Vlan100
docker exec clab-sonic-test-s1 grep '|c|SAI_OBJECT_TYPE_VLAN' /var/log/swss/sairedis.rec
docker exec clab-sonic-test-s1 vtysh -c "show running-config"
```
