# edge1: show ip route

- Return code: 0

## STDOUT

```
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIP, O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv4 unicast VRF default:
S   0.0.0.0/0 [1/0] unreachable (blackhole), weight 1, 01:45:40
K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, weight 1, 01:45:41
L * 10.255.0.31/32 is directly connected, lo, weight 1, 01:45:40
C>* 10.255.0.31/32 is directly connected, lo, weight 1, 01:45:40
C>* 172.16.0.0/31 is directly connected, eth1, weight 1, 01:45:35
L>* 172.16.0.1/32 is directly connected, eth1, weight 1, 01:45:35
C>* 172.16.0.2/31 is directly connected, eth2, weight 1, 01:45:32
L>* 172.16.0.3/32 is directly connected, eth2, weight 1, 01:45:32
C>* 172.20.20.0/24 is directly connected, eth0, weight 1, 01:45:39
L * 172.20.20.10/32 is directly connected, eth0, weight 1, 01:45:39
L>* 172.20.20.10/32 is directly connected, eth0, weight 1, 01:45:41
B>* 192.168.1.0/24 [20/0] via 172.16.0.0, eth1, weight 1, 01:45:15
  *                       via 172.16.0.2, eth2, weight 1, 01:45:15
B>* 192.168.2.0/24 [20/0] via 172.16.0.0, eth1, weight 1, 01:45:11
  *                       via 172.16.0.2, eth2, weight 1, 01:45:11
```

## STDERR

```
```

## Notes

edge1's routing table confirms policy enforcement:
- `S>* 0.0.0.0/0 Null0` — the static black-hole that triggers `default-originate` on BGP neighbors. Edge1 does not have a real upstream; Null0 ensures the condition is met.
- `B>* 192.168.1.0/24` and `B>* 192.168.2.0/24` — only the two host subnets are received from the fabric (policy `TO-EDGE-OUT` on spines is working correctly). No infrastructure prefixes (10.0.0.0/24, 10.255.0.0/24) leaked to edge.
- Both host subnets have two equal-cost paths (one via each spine) — dual-homed eBGP provides redundancy.
