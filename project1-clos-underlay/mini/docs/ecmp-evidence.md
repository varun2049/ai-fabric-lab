
# ECMP LOGS


## TEST 1

=== BEFORE ===
spine1 eth2 TX: 906997
spine2 eth2 TX: 24074468913
Connecting to host 192.168.12.10, port 5201

=== AFTER ===
spine1 eth2 TX: 909479
spine2 eth2 TX: 58895226774

## TEST 2
 
=== BEFORE ===
spine1: 926169
spine2: 87321594004
Connecting to host 192.168.12.11, port 5202
Connecting to host 192.168.12.10, port 5201
Connecting to host 192.168.12.13, port 5204
Connecting to host 192.168.12.12, port 5203

=== AFTER ===
spine1: 52533797334
spine2: 139711753265

## RESULTS

Entropy is set by how the flows differ, visible in the "Connecting to" lines:
- Test 1 (low entropy): all 8 flows → same dst 192.168.12.10:5201, only src port varied.
- Test 2 (high entropy): 4 flows → varied dst IP and dst port (.10:5201, .11:5202, .12:5203, .13:5204).

Deltas (AFTER − BEFORE):
- Test 1: spine1 ≈ 0, spine2 ≈ 34.8 GB → all traffic polarized onto one spine.
- Test 2: spine1 ≈ 52.5 GB, spine2 ≈ 52.4 GB → even ~50/50 split.

ECMP hashes on the 5 tuple, so spread depends on flow entropy.
Low entropy (few varying fields) collides flows onto one path; high entropy
spreads them.

```
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 pkill iperf3 2>/dev/null; sleep 1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== BEFORE ==="
=== BEFORE ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1 eth2 TX: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1 eth2 TX: 906997
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2 eth2 TX: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2 eth2 TX: 24074468913
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h1 iperf3 -c 192.168.12.10 -t 15 -P 8
Connecting to host 192.168.12.10, port 5201
[  5] local 192.168.11.10 port 58380 connected to 192.168.12.10 port 5201
[  7] local 192.168.11.10 port 58394 connected to 192.168.12.10 port 5201
[  9] local 192.168.11.10 port 58404 connected to 192.168.12.10 port 5201
[ 11] local 192.168.11.10 port 58410 connected to 192.168.12.10 port 5201
[ 13] local 192.168.11.10 port 58422 connected to 192.168.12.10 port 5201
[ 15] local 192.168.11.10 port 58432 connected to 192.168.12.10 port 5201
[ 17] local 192.168.11.10 port 58440 connected to 192.168.12.10 port 5201
[ 19] local 192.168.11.10 port 58448 connected to 192.168.12.10 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    268 KBytes       
[  7]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    268 KBytes       
[  9]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 11]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 13]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 15]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    258 KBytes       
[ 17]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 19]   0.00-1.00   sec   282 MBytes  2.37 Gbits/sec    0    258 KBytes       
[SUM]   0.00-1.00   sec  2.21 GBytes  18.9 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    277 KBytes       
[  7]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    268 KBytes       
[  9]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 11]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 13]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 15]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    258 KBytes       
[ 17]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 19]   1.00-2.00   sec   284 MBytes  2.38 Gbits/sec    0    258 KBytes       
[SUM]   1.00-2.00   sec  2.22 GBytes  19.0 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    277 KBytes       
[  7]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    268 KBytes       
[  9]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    498 KBytes       
[ 11]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    498 KBytes       
[ 13]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    498 KBytes       
[ 15]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    258 KBytes       
[ 17]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    498 KBytes       
[ 19]   2.00-3.00   sec   280 MBytes  2.35 Gbits/sec    0    258 KBytes       
[SUM]   2.00-3.00   sec  2.19 GBytes  18.8 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    277 KBytes       
[  7]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    277 KBytes       
[  9]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 11]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 13]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 15]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    268 KBytes       
[ 17]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 19]   3.00-4.00   sec   282 MBytes  2.37 Gbits/sec    0    268 KBytes       
[SUM]   3.00-4.00   sec  2.21 GBytes  18.9 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    277 KBytes       
[  7]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    277 KBytes       
[  9]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 11]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 13]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 15]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    268 KBytes       
[ 17]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    498 KBytes       
[ 19]   4.00-5.00   sec   284 MBytes  2.37 Gbits/sec    0    268 KBytes       
[SUM]   4.00-5.00   sec  2.22 GBytes  19.0 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    1    295 KBytes       
[  7]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    1    295 KBytes       
[  9]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 11]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 13]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    498 KBytes       
[ 15]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    295 KBytes       
[ 17]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    517 KBytes       
[ 19]   5.00-6.00   sec   282 MBytes  2.38 Gbits/sec    0    314 KBytes       
[SUM]   5.00-6.00   sec  2.21 GBytes  19.0 Gbits/sec    2             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    295 KBytes       
[  7]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    295 KBytes       
[  9]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    498 KBytes       
[ 11]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    498 KBytes       
[ 13]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    498 KBytes       
[ 15]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    295 KBytes       
[ 17]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    517 KBytes       
[ 19]   6.00-7.00   sec   280 MBytes  2.34 Gbits/sec    0    314 KBytes       
[SUM]   6.00-7.00   sec  2.19 GBytes  18.7 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   7.00-8.00   sec   279 MBytes  2.35 Gbits/sec    0    295 KBytes       
[  7]   7.00-8.00   sec   279 MBytes  2.35 Gbits/sec    0    351 KBytes       
[  9]   7.00-8.00   sec   280 MBytes  2.35 Gbits/sec    0    544 KBytes       
[ 11]   7.00-8.00   sec   279 MBytes  2.35 Gbits/sec    0    544 KBytes       
[ 13]   7.00-8.00   sec   280 MBytes  2.35 Gbits/sec   21    544 KBytes       
[ 15]   7.00-8.00   sec   279 MBytes  2.35 Gbits/sec    0    360 KBytes       
[ 17]   7.00-8.00   sec   280 MBytes  2.35 Gbits/sec    0    600 KBytes       
[ 19]   7.00-8.00   sec   279 MBytes  2.35 Gbits/sec    0    397 KBytes       
[SUM]   7.00-8.00   sec  2.18 GBytes  18.8 Gbits/sec   21             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   8.00-9.00   sec   278 MBytes  2.34 Gbits/sec    0    295 KBytes       
[  7]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    351 KBytes       
[  9]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    544 KBytes       
[ 11]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    544 KBytes       
[ 13]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    544 KBytes       
[ 15]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    360 KBytes       
[ 17]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    600 KBytes       
[ 19]   8.00-9.00   sec   278 MBytes  2.33 Gbits/sec    0    397 KBytes       
[SUM]   8.00-9.00   sec  2.17 GBytes  18.7 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    277 KBytes       
[  7]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    268 KBytes       
[  9]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    544 KBytes       
[ 11]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    544 KBytes       
[ 13]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    544 KBytes       
[ 15]   9.00-10.00  sec   238 MBytes  2.00 Gbits/sec    3    360 KBytes       
[ 17]   9.00-10.00  sec   239 MBytes  2.00 Gbits/sec    3    600 KBytes       
[ 19]   9.00-10.00  sec   239 MBytes  2.00 Gbits/sec    3    397 KBytes       
[SUM]   9.00-10.00  sec  1.86 GBytes  16.0 Gbits/sec   24             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]  10.00-11.00  sec   269 MBytes  2.26 Gbits/sec    0    277 KBytes       
[  7]  10.00-11.00  sec   269 MBytes  2.26 Gbits/sec    0    286 KBytes       
[  9]  10.00-11.00  sec   269 MBytes  2.26 Gbits/sec    0    544 KBytes       
[ 11]  10.00-11.00  sec   269 MBytes  2.26 Gbits/sec    0    544 KBytes       
[ 13]  10.00-11.00  sec   269 MBytes  2.25 Gbits/sec    0    544 KBytes       
[ 15]  10.00-11.00  sec   269 MBytes  2.26 Gbits/sec    0    360 KBytes       
[ 17]  10.00-11.00  sec   269 MBytes  2.25 Gbits/sec    0    600 KBytes       
[ 19]  10.00-11.00  sec   269 MBytes  2.25 Gbits/sec    0    397 KBytes       
[SUM]  10.00-11.00  sec  2.10 GBytes  18.1 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    295 KBytes       
[  7]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    304 KBytes       
[  9]  11.00-12.00  sec   268 MBytes  2.24 Gbits/sec    0    544 KBytes       
[ 11]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    544 KBytes       
[ 13]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    544 KBytes       
[ 15]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    360 KBytes       
[ 17]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    600 KBytes       
[ 19]  11.00-12.00  sec   268 MBytes  2.25 Gbits/sec    0    397 KBytes       
[SUM]  11.00-12.00  sec  2.09 GBytes  18.0 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    295 KBytes       
[  7]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    304 KBytes       
[  9]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    544 KBytes       
[ 11]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    544 KBytes       
[ 13]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    544 KBytes       
[ 15]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    360 KBytes       
[ 17]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    600 KBytes       
[ 19]  12.00-13.00  sec   273 MBytes  2.29 Gbits/sec    0    397 KBytes       
[SUM]  12.00-13.00  sec  2.13 GBytes  18.3 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]  13.00-14.00  sec   273 MBytes  2.29 Gbits/sec    0    295 KBytes       
[  7]  13.00-14.00  sec   272 MBytes  2.28 Gbits/sec    0    323 KBytes       
[  9]  13.00-14.00  sec   272 MBytes  2.29 Gbits/sec    0    544 KBytes       
[ 11]  13.00-14.00  sec   272 MBytes  2.28 Gbits/sec    0    544 KBytes       
[ 13]  13.00-14.00  sec   273 MBytes  2.29 Gbits/sec    0    544 KBytes       
[ 15]  13.00-14.00  sec   272 MBytes  2.28 Gbits/sec    0    360 KBytes       
[ 17]  13.00-14.00  sec   273 MBytes  2.29 Gbits/sec    0    600 KBytes       
[ 19]  13.00-14.00  sec   272 MBytes  2.29 Gbits/sec    0    397 KBytes       
[SUM]  13.00-14.00  sec  2.13 GBytes  18.3 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]  14.00-15.00  sec   270 MBytes  2.26 Gbits/sec    0    295 KBytes       
[  7]  14.00-15.00  sec   270 MBytes  2.26 Gbits/sec    0    323 KBytes       
[  9]  14.00-15.00  sec   270 MBytes  2.26 Gbits/sec    0    544 KBytes       
[ 11]  14.00-15.00  sec   270 MBytes  2.27 Gbits/sec    0    544 KBytes       
[ 13]  14.00-15.00  sec   269 MBytes  2.26 Gbits/sec    0    544 KBytes       
[ 15]  14.00-15.00  sec   270 MBytes  2.26 Gbits/sec    0    360 KBytes       
[ 17]  14.00-15.00  sec   269 MBytes  2.26 Gbits/sec    0    600 KBytes       
[ 19]  14.00-15.00  sec   269 MBytes  2.26 Gbits/sec    0    397 KBytes       
[SUM]  14.00-15.00  sec  2.11 GBytes  18.1 Gbits/sec    0             
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    4             sender
[  5]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[  7]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    4             sender
[  7]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[  9]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    3             sender
[  9]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[ 11]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    3             sender
[ 11]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[ 13]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec   24             sender
[ 13]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[ 15]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    3             sender
[ 15]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[ 17]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    3             sender
[ 17]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[ 19]   0.00-15.00  sec  4.03 GBytes  2.31 Gbits/sec    3             sender
[ 19]   0.00-15.00  sec  4.02 GBytes  2.30 Gbits/sec                  receiver
[SUM]   0.00-15.00  sec  32.2 GBytes  18.4 Gbits/sec   47             sender
[SUM]   0.00-15.00  sec  32.2 GBytes  18.4 Gbits/sec                  receiver

iperf Done.
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== AFTER ==="
=== AFTER ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1 eth2 TX: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1 eth2 TX: 909479
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2 eth2 TX: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2 eth2 TX: 58895226774
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 ip addr add 192.168.12.11/24 dev eth1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 ip addr add 192.168.12.12/24 dev eth1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 ip addr add 192.168.12.13/24 dev eth1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 pkill iperf3 2>/dev/null; sleep 1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== BEFORE ==="
=== BEFORE ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1 eth2 TX: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1 eth2 TX: 919983
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2 eth2 TX: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2 eth2 TX: 58895235939
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h1 sh -c "iperf3 -c 192.168.12.10 -t 12 & iperf3 -c 192.168.12.11 -t 12 & iperf3 -c 192.168.12.12 -t 12 & iperf3 -c 192.168.12.13 -t 12 & wait"
Connecting to host 192.168.12.10, port 5201
iperf3: error - the server is busy running a test. try again later
iperf3: error - the server is busy running a test. try again later
iperf3: error - the server is busy running a test. try again later
[  5] local 192.168.11.10 port 33212 connected to 192.168.12.10 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.23 GBytes  19.1 Gbits/sec    0   1006 KBytes       
[  5]   1.00-2.00   sec  2.25 GBytes  19.4 Gbits/sec    0   1006 KBytes       
[  5]   2.00-3.00   sec  2.25 GBytes  19.3 Gbits/sec    0   1.20 MBytes       
[  5]   3.00-4.00   sec  2.18 GBytes  18.7 Gbits/sec    0   1.89 MBytes       
[  5]   4.00-5.00   sec  2.24 GBytes  19.2 Gbits/sec    0   2.30 MBytes       
[  5]   5.00-6.00   sec  2.03 GBytes  17.4 Gbits/sec    0   2.30 MBytes       
[  5]   6.00-7.00   sec  2.22 GBytes  19.1 Gbits/sec    0   2.30 MBytes       
[  5]   7.00-8.00   sec  2.20 GBytes  18.9 Gbits/sec    0   2.53 MBytes       
[  5]   8.00-9.00   sec  2.13 GBytes  18.3 Gbits/sec   73   2.79 MBytes       
[  5]   9.00-10.00  sec  2.11 GBytes  18.1 Gbits/sec    0   2.79 MBytes       
[  5]  10.00-11.00  sec  2.21 GBytes  19.0 Gbits/sec    0   2.79 MBytes       
[  5]  11.00-12.00  sec  2.23 GBytes  19.2 Gbits/sec  132   2.79 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-12.00  sec  26.3 GBytes  18.8 Gbits/sec  205             sender
[  5]   0.00-12.00  sec  26.3 GBytes  18.8 Gbits/sec                  receiver

iperf Done.
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== AFTER ==="
=== AFTER ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1 eth2 TX: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1 eth2 TX: 922847
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2 eth2 TX: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2 eth2 TX: 87321591257
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h2 pkill iperf3 2>/dev/null; sleep 1
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s -p 5201
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s -p 5202
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s -p 5203
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec -d clab-p1-mini-h2 iperf3 -s -p 5204
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== BEFORE ==="
=== BEFORE ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1: 926169
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2: 87321594004
robot@clab:~/netlab/project1-clos-underlay/mini$ docker exec clab-p1-mini-h1 sh -c "iperf3 -c 192.168.12.10 -p 5201 -t 12 & iperf3 -c 192.168.12.11 -p 5202 -t 12 & iperf3 -c 192.168.12.12 -p 5203 -t 12 & iperf3 -c 192.168.12.13 -p 5204 -t 12 & wait"
Connecting to host 192.168.12.11, port 5202
Connecting to host 192.168.12.10, port 5201
Connecting to host 192.168.12.13, port 5204
Connecting to host 192.168.12.12, port 5203
[  5] local 192.168.11.10 port 36618 connected to 192.168.12.13 port 5204
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.02 GBytes  17.3 Gbits/sec   13   2.49 MBytes       
[  5]   1.00-2.00   sec  2.10 GBytes  18.0 Gbits/sec    0   2.52 MBytes       
[  5]   2.00-3.00   sec  2.10 GBytes  18.0 Gbits/sec   38   2.54 MBytes       
[  5]   3.00-4.00   sec  2.09 GBytes  18.0 Gbits/sec  129   2.54 MBytes       
[  5]   4.00-5.00   sec  2.09 GBytes  18.0 Gbits/sec  212   2.54 MBytes       
[  5]   5.00-6.00   sec  2.09 GBytes  18.0 Gbits/sec   17   2.54 MBytes       
[  5]   6.00-7.00   sec  2.10 GBytes  18.1 Gbits/sec  130   2.58 MBytes       
[  5]   7.00-8.00   sec  2.05 GBytes  17.6 Gbits/sec    0   2.58 MBytes       
[  5]   8.00-9.00   sec  1.84 GBytes  15.8 Gbits/sec   32   2.58 MBytes       
[  5]   9.00-10.00  sec  1.81 GBytes  15.5 Gbits/sec  107   2.59 MBytes       
[  5]  10.00-11.00  sec  1.90 GBytes  16.4 Gbits/sec  231   2.61 MBytes       
[  5]  11.00-12.00[  5] local 192.168.11.10 port 49598 connected to 192.168.12.12 port 5203
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.00 GBytes  17.2 Gbits/sec    0   1.95 MBytes       
[  5]   1.00-2.00   sec  2.09 GBytes  17.9 Gbits/sec   88   2.08 MBytes       
[  5]   2.00-3.00   sec  2.10 GBytes  18.0 Gbits/sec  252   2.11 MBytes       
[  5]   3.00-4.00   sec  2.10 GBytes  18.0 Gbits/sec  152   2.11 MBytes       
[  5]   4.00-5.00   sec  2.09 GBytes  18.0 Gbits/sec   96   2.11 MBytes       
[  5]   5.00-6.00   sec  2.09 GBytes  18.0 Gbits/sec    0   2.11 MBytes       
[  5]   6.00-7.00   sec  2.10 GBytes  18.0 Gbits/sec  295   2.11 MBytes       
[  5]   7.00-8.00   sec  2.06 GBytes  17.7 Gbits/sec  141   2.11 MBytes       
[  5]   8.00-9.00   sec  1.83 GBytes  15.8 Gbits/sec  482   2.11 MBytes       
[  5]   9.00-10.00  sec  1.77 GBytes  15.2 Gbits/sec   71   2.11 MBytes       
[  5]  10.00-11.00  sec  1.90 GBytes  16.3 Gbits/sec  402   2.13 MBytes       
[  5]  11.00-12.00  sec  2.06 GBytes  17.7 Gbits/sec    0   2.14 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-12.00  sec  24.2 GBytes  17.3 Gbits/sec  1979             sender
[  5]   0.00-12.00  sec  24.2 GBytes  17.3 Gbits/sec                  receiver

iperf Done.
[  5] local 192.168.11.10 port 60528 connected to 192.168.12.10 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.01 GBytes  17.3 Gbits/sec    0   2.38 MBytes       
[  5]   1.00-2.00   sec  2.10 GBytes  18.1 Gbits/sec    0   3.24 MBytes       
[  5]   2.00-3.00   sec  2.09 GBytes  18.0 Gbits/sec    0   3.41 MBytes       
[  5]   3.00-4.00   sec  2.09 GBytes  18.0 Gbits/sec    0   3.57 MBytes       
[  5]   4.00-5.00   sec  2.10 GBytes  18.0 Gbits/sec    0   3.75 MBytes       
[  5]   5.00-6.00   sec  2.07 GBytes  17.8 Gbits/sec    0   3.94 MBytes       
[  5]   6.00-7.00   sec  2.10 GBytes  18.0 Gbits/sec    0   3.94 MBytes       
[  5]   7.00-8.00   sec  2.06 GBytes  17.7 Gbits/sec    0   3.94 MBytes       
[  5]   8.00-9.00   sec  1.85 GBytes  15.9 Gbits/sec    0   3.94 MBytes       
[  5]   9.00-10.00  sec  1.79 GBytes  15.3 Gbits/sec    0   3.94 MBytes       
[  5]  10.00-11.00  sec  1.90 GBytes  16.3 Gbits/sec    0   3.94 MBytes       
[  5]  11.00-12.00  sec  2.08 GBytes  17.8 Gbits/sec    0   3.94 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-12.00  sec  24.2 GBytes  17.4 Gbits/sec    0             sender
[  5]   0.00-12.00  sec  24.2 GBytes  17.4 Gbits/sec                  receiver

iperf Done.
  sec  2.06 GBytes  17.7 Gbits/sec   70   2.61 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-12.00  sec  24.3 GBytes  17.4 Gbits/sec  979             sender
[  5]   0.00-12.00  sec  24.3 GBytes  17.4 Gbits/sec                  receiver

iperf Done.
[  5] local 192.168.11.10 port 34534 connected to 192.168.12.11 port 5202
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.03 GBytes  17.5 Gbits/sec   12   2.41 MBytes       
[  5]   1.00-2.00   sec  2.09 GBytes  17.9 Gbits/sec  107   2.41 MBytes       
[  5]   2.00-3.00   sec  2.09 GBytes  17.9 Gbits/sec  107   2.41 MBytes       
[  5]   3.00-4.00   sec  2.11 GBytes  18.2 Gbits/sec  189   2.41 MBytes       
[  5]   4.00-5.00   sec  2.09 GBytes  17.9 Gbits/sec  298   2.41 MBytes       
[  5]   5.00-6.00   sec  2.10 GBytes  18.0 Gbits/sec  120   2.41 MBytes       
[  5]   6.00-7.00   sec  2.11 GBytes  18.2 Gbits/sec   13   2.42 MBytes       
[  5]   7.00-8.00   sec  2.05 GBytes  17.6 Gbits/sec  115   2.44 MBytes       
[  5]   8.00-9.00   sec  1.83 GBytes  15.7 Gbits/sec  179   2.44 MBytes       
[  5]   9.00-10.00  sec  1.78 GBytes  15.3 Gbits/sec  230   2.44 MBytes       
[  5]  10.00-11.00  sec  1.92 GBytes  16.5 Gbits/sec   95   2.44 MBytes       
[  5]  11.00-12.00  sec  2.08 GBytes  17.9 Gbits/sec    0   2.44 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-12.00  sec  24.3 GBytes  17.4 Gbits/sec  1465             sender
[  5]   0.00-12.00  sec  24.3 GBytes  17.4 Gbits/sec                  receiver

iperf Done.
robot@clab:~/netlab/project1-clos-underlay/mini$ echo "=== AFTER ==="
=== AFTER ===
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine1: "; docker exec clab-p1-mini-spine1 cat /sys/class/net/eth2/statistics/tx_bytes
spine1: 52533797334
robot@clab:~/netlab/project1-clos-underlay/mini$ echo -n "spine2: "; docker exec clab-p1-mini-spine2 cat /sys/class/net/eth2/statistics/tx_bytes
spine2: 139711753265
```

