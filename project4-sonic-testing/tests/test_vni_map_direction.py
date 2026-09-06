"""Original DVS test - Project 4.

Encodes two behaviours read from sonic-swss/orchagent/vxlanorch.cpp (branch 202411):

  1. VxlanTunnelMapOrch::addOperation creates exactly ONE tunnel-map entry for an
     L2 VNI, in the decapsulation direction (VNI_TO_VLAN_ID). No VLAN_ID_TO_VNI entry.
  2. VxlanVrfMapOrch::addOperation, on binding a VRF to that VNI, removes the VLAN
     map entry and creates VNI <-> VIRTUAL_ROUTER entries in its place.

Run via the runner:  ./run-dvs.sh -v local/test_vni_map_direction.py
"""
import time
from swsscommon import swsscommon
from evpn_tunnel import VxlanTunnel

ASIC_MAP_ENTRY = "ASIC_STATE:SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY"

def map_entries_for_vni(dvs, vni):
    """All tunnel-map entries in ASIC_DB whose VNI key is `vni`: {oid: attrs}."""
    asic_db = swsscommon.DBConnector(swsscommon.ASIC_DB, dvs.redis_sock, 0)
    tbl = swsscommon.Table(asic_db, ASIC_MAP_ENTRY)
    found = {}
    for key in tbl.getKeys():
        _, fvs = tbl.get(key)
        attrs = dict(fvs)
        if attrs.get("SAI_TUNNEL_MAP_ENTRY_ATTR_VNI_ID_KEY") == vni:
            found[key] = attrs
    return found

def map_types_for_vni(dvs, vni):
    return sorted(a["SAI_TUNNEL_MAP_ENTRY_ATTR_TUNNEL_MAP_TYPE"]
                  for a in map_entries_for_vni(dvs, vni).values())


class TestVniMapDirection(object):

    def test_l2_vni_creates_single_decap_entry(self, dvs, testlog):
        vx = VxlanTunnel()
        vx.fetch_exist_entries(dvs)

        vx.create_vlan1(dvs, "Vlan100")
        vx.check_vlan_obj(dvs, "100")
        vx.create_vxlan_tunnel(dvs, "tunnel_1", "10.255.0.11")
        vx.create_evpn_nvo(dvs, "nvo1", "tunnel_1")
        vx.create_vxlan_tunnel_map(dvs, "tunnel_1", "map_100_Vlan100", "100", "Vlan100")

        # upstream helpers: the SIP tunnel and its decap entry exist (the first call also
        # caches the tunnel's map OIDs, which the second one needs)
        vx.check_vxlan_sip_tunnel(dvs, "tunnel_1", "10.255.0.11", ["100"], ["100"], tunnel_map_entry_count=1)
        vx.check_vxlan_tunnel_map_entry(dvs, "tunnel_1", ["100"], ["100"])

        # the finding: exactly one entry for this VNI, and it is the decap direction
        types = map_types_for_vni(dvs, "100")
        assert types == ["SAI_TUNNEL_MAP_TYPE_VNI_TO_VLAN_ID"], \
            f"expected one VNI_TO_VLAN_ID entry for VNI 100, found {types}"

        vx.remove_vxlan_tunnel_map(dvs, "tunnel_1", "map_100_Vlan100", "100", "Vlan100")
        vx.remove_evpn_nvo(dvs, "nvo1")
        vx.remove_vxlan_tunnel(dvs, "tunnel_1")
        vx.remove_vlan(dvs, "100")

    def test_vrf_binding_replaces_vlan_entry(self, dvs, testlog):
        vx = VxlanTunnel()
        vx.fetch_exist_entries(dvs)

        vx.create_vlan1(dvs, "Vlan1000")
        vx.check_vlan_obj(dvs, "1000")
        vx.create_vxlan_tunnel(dvs, "tunnel_1", "10.255.0.11")
        vx.create_evpn_nvo(dvs, "nvo1", "tunnel_1")
        vx.create_vxlan_tunnel_map(dvs, "tunnel_1", "map_1000_Vlan1000", "1000", "Vlan1000")
        vx.check_vxlan_sip_tunnel(dvs, "tunnel_1", "10.255.0.11", ["1000"], ["1000"], tunnel_map_entry_count=1)
        vx.check_vxlan_tunnel_map_entry(dvs, "tunnel_1", ["1000"], ["1000"])
        assert map_types_for_vni(dvs, "1000") == ["SAI_TUNNEL_MAP_TYPE_VNI_TO_VLAN_ID"]

        # bind a VRF to the same VNI: the VLAN entry must go, a VRF entry must appear
        vx.create_vrf(dvs, "VrfA")
        vx.create_vxlan_vrf_tunnel_map(dvs, "VrfA", "1000")
        vx.check_vxlan_tunnel_vrf_map_entry(dvs, "tunnel_1", "VrfA", "1000")
        time.sleep(2)

        types = map_types_for_vni(dvs, "1000")
        assert "SAI_TUNNEL_MAP_TYPE_VNI_TO_VLAN_ID" not in types, \
            f"VLAN map entry should have been removed by VxlanVrfMapOrch, found {types}"
        assert "SAI_TUNNEL_MAP_TYPE_VNI_TO_VIRTUAL_ROUTER_ID" in types, \
            f"expected a VNI_TO_VIRTUAL_ROUTER_ID entry for VNI 1000, found {types}"

        vx.remove_vxlan_vrf_tunnel_map(dvs, "VrfA")
        vx.remove_vrf(dvs, "VrfA")
        vx.remove_vxlan_tunnel_map(dvs, "tunnel_1", "map_1000_Vlan1000", "1000", "Vlan1000")
        vx.remove_evpn_nvo(dvs, "nvo1")
        vx.remove_vxlan_tunnel(dvs, "tunnel_1")
        vx.remove_vlan(dvs, "1000")
