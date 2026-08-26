# EVPN Type-5 Routes - Project 2.5

## What this shows
Type-2 routes advertise hosts the fabric has learned. Type-5 routes (RFC 9136)
advertise IP prefixes - subnets, externals, summaries - and are the safety net for
silent hosts: without them, an ingress leaf that does not carry the destination subnet
has nothing to route on. This documents Type-5s on the wire-facing control plane, how
they land in the tenant VRF, and both route types coexisting.

## Evidence 1 - Type-5 routes in the EVPN table

```
Route Distinguisher: 192.168.101.1:2
 *>  [5]:[0]:[24]:[192.168.101.0]
                    10.255.0.12(spine1)
                                                           0 65100 65012 ?
                    RT:65012:1000 ET:8 Rmac:aa:bb:cc:00:00:12
 *=  [5]:[0]:[24]:[192.168.101.0]
                    10.255.0.12(spine2)
                                                           0 65100 65012 ?
                    RT:65012:1000 ET:8 Rmac:aa:bb:cc:00:00:12
```

Reading the route:
- `[5]:[0]:[24]:[192.168.101.0]` - a prefix, no MAC in the key. The pure-L3 member of
  the EVPN family.
- `RT:65012:1000` - the L3 route-target, auto-derived from the L3VNI (1000), not an
  L2VNI. This is what steers the route into VRF tenantA on import rather than into a
  bridge domain. Tenant B's Type-5s carry RT:...:2000 and land in tenantB only.
- `Rmac:aa:bb:cc:00:00:12` - leaf2's router MAC as an extended community. This tells
  the importing leaf what inner destination MAC to write when routing to this prefix.
- Origin `?` (incomplete) - the route entered BGP via `redistribute connected` in the
  VRF instance, not a network statement.
- `*>` / `*=` - both spine paths installed. Project 1's shared-spine-ASN ECMP design,
  now operating on Type-5 routes.
- RD `192.168.101.1:2` - derived from the VRF instance's SVI IP rather than the
  router-id.

The VRF BGP instance that originates these has no neighbors - it exports into the
default instance, whose existing underlay sessions carry the routes fabric-wide.

## Evidence 2 - installed in the tenant VRF over the L3VNI

```
VRF tenantA:
B>* 192.168.101.0/24 [20/0] via 10.255.0.12, br1000 onlink, weight 1, 00:02:32
                            via 10.255.0.12, br1000 onlink, weight 1, 00:02:32
```

A route in tenant A's table, next-hop leaf2's loopback, installed over br1000 - the
L3VNI's SVI. leaf1 has no bridge for subnet 101 and reaches it only by routing over
this interface. `onlink` because the VTEP address is not on the SVI's subnet (the
L3VNI is subnetless); the kernel is told to use the interface anyway.

## Evidence 3 - Type-5 and Type-2 coexisting

```
VRF tenantB:
B>* 192.168.201.0/24 [20/0] via 10.255.0.12, br2000 onlink, weight 1, 00:35:32
B>* 192.168.201.10/32 [20/0] via 10.255.0.12, br2000 onlink, weight 1, 00:00:04
```

The /24 is a Type-5, present since the fabric converged (35 minutes). The /32 is a
host route from h4's MAC+IP Type-2, four seconds old - it appeared the moment h4
transmitted and leaf2 learned it locally. Longest-prefix-match prefers the /32 when
present; the /24 covers the silent-host case. They layer; neither replaces the other.
The 4-second timestamp is the Type-2 lifecycle from Project 2 (advertisement tied to
live local learning) in its routed form.

## What was proven
1 Prefixes propagate through EVPN as Type-5 routes carrying an L3-RT and the
originator's router MAC, relayed by the same underlay sessions as everything else.
2 Import lands them in the correct tenant VRF, installed over the L3VNI SVI.
3 Host routes (/32, Type-2-derived) and subnet routes (/24, Type-5) coexist, with LPM
selecting the host route when the host has been learned.

## Limitation
All Type-5s here are redistributed connected subnets. External or summarised prefixes
(the border-leaf use case) are not exercised.

## Commands used

```
docker exec clab-p25-irb-leaf1 vtysh -c "show bgp l2vpn evpn route type prefix"
docker exec clab-p25-irb-leaf1 vtysh -c "show ip route vrf tenantA"
docker exec clab-p25-irb-leaf1 vtysh -c "show ip route vrf tenantB"
```
