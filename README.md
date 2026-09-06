# AI Fabric Lab

Hands-on portfolio in AI data-center networking: an EVPN-VXLAN leaf-spine fabric built
from the underlay up, moved onto SONiC, opened to the SAI call, and validated with
SONiC's own test frameworks. Every project is reproducible from this repository and
documented with verbatim evidence.

| # | Project | What it builds | What it proves |
|---|---|---|---|
| 1 | [Clos underlay](project1-clos-underlay/) | eBGP leaf-spine, /31 links, ECMP, BFD | Failure detection 6.86 s to 0.84 s with BFD, measured with a purpose-built probe; ECMP spread governed by flow entropy |
| 2 | [VXLAN/EVPN L2](project2-vxlan-evpn-l2/) | Static VXLAN, then EVPN control plane, two tenants | Type-2 and Type-3 routes correlated with kernel state and packets; ARP suppression and flood-and-learn measured |
| 2.5 | [Symmetric IRB + Type-5](project2_5-frr-irb-type5/) | VRFs, L3VNIs, anycast gateways, prefix routes | Routed overlay proven at ttl=62; a gateway-MAC conflict root-caused against vendor documentation |
| 3 | [SONiC internals](project3-sonic-internals/) | The same fabric on SONiC; configuration traced CONFIG_DB to kernel to APPL_DB to ASIC_DB to the SAI recording | A route, a remote MAC and a VNI map located in every layer; the orchagent code behind each SAI call annotated; snapshot and Prometheus tools |
| 4 | [SONiC testing](project4-sonic-testing/) | DVS, PTF and SPyTest against the SONiC fabric | 16 upstream DVS tests passing plus original tests at all three layers, on a community build the frameworks were not written for |

## How it fits together
Projects 1 to 2.5 build the fabric on FRR and Linux, where every table is a kernel
command away. Project 3 rebuilds it on SONiC and follows the same state through the
NOS to the chip boundary. Project 4 puts that fabric under the community's test
tooling. The method is constant: build, measure, read the tables, correlate the
layers, document what was seen.

## Environment
containerlab throughout; FRR for the spines and for all of Projects 1 to 2.5;
`docker-sonic-vs` (community 202411) for the SONiC leaves; multitool containers as
hosts. Projects 1 to 2.5 run on Apple silicon; Projects 3 and 4 run on x86-64 (WSL2),
which the SONiC image requires.

## Layout
Each project has a topology, configurations and a setup script, a `docs/` directory
of evidence, and a README stating what it proves, how to run it, and its limitations.
