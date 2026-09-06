# Project 1 - eBGP Leaf-Spine Clos Underlay

A data-center underlay built with FRRouting and containerlab: two spines, two leaves,
eBGP on every link, ECMP across spines. The fabric that Projects 2 onward build their
overlays on, and the one in which failure detection was measured.

```
    spine1 (AS65100)   spine2 (AS65100)
       |    \           /    |
    leaf1 (AS65011)  leaf2 (AS65012)
       |                 |
      h1                h2
  192.168.11.10     192.168.12.10
```

Spines share one ASN and each leaf has its own (RFC 7938), so the two paths to any
remote subnet carry identical AS_PATHs and both install. Links are /31s; loopbacks are
router IDs and, in later projects, VTEP addresses.

## What this proves

- **BFD cuts failure detection from 6.86 s to 0.84 s** (median of three trials each),
  an 88% reduction, measured with a probe that polls the peer state every 50 ms after
  pausing a spine. Both numbers land where the timers predict: a 9 s hold timer
  expiring mid-cycle, and a 300 ms x 3 BFD window.
- **ECMP spread depends on flow entropy.** Eight flows to one destination and port
  polarized onto a single spine (~0 vs 34.8 GB); four flows across varied addresses
  and ports split evenly (52.5 vs 52.4 GB). The hash is the 5-tuple; the traffic
  decides.
- **Failure handling is next-hop deactivation, not recomputation.** With both paths
  pre-installed, a link cut marks one next-hop `inactive` and forwarding continues on
  the other: 40 probes, none lost.
- **One measurement remains open.** A data-plane test showed a 16 s outage that ended
  only when the failed link was restored - longer than detection explains. Two
  candidate causes are recorded in the report; neither has been isolated.

## Layout
```
project1-clos-underlay/
  topology.clab.yml      two spines, two leaves, two hosts
  configs/               FRR configuration per node
  tests/                 detection.py, convergence.py, plot_convergence.py
  docs/                  evidence documents
```

## Documentation
1. [convergence-report.md](docs/convergence-report.md) - detection time with default
   timers and with BFD; method, timer arithmetic, the open data-plane item
2. [convergence-evidence.md](docs/convergence-evidence.md) - link failure with ECMP
   pre-installed paths
3. [ecmp-evidence.md](docs/ecmp-evidence.md) - traffic spread versus flow entropy

## How to run
Requires containerlab and Docker.

```
sudo containerlab deploy -t topology.clab.yml
docker exec clab-p1-mini-spine1 vtysh -c "show bgp summary"
docker exec clab-p1-mini-h1 ping -c 3 192.168.12.10
python3 tests/detection.py                 # detection time, three trials
sudo containerlab destroy -t topology.clab.yml --cleanup
```

## Limitations
A virtual lab measures control-plane detection and kernel forwarding, not ASIC
convergence. Two spines and two leaves show the mechanisms; ECMP behaviour with many
flows and many paths is not represented. The open data-plane finding is documented,
not resolved.
