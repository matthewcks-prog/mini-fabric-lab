# spine1: show ip route

- Return code: 0

## STDOUT

```
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIP, O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

K>* 0.0.0.0/0 [0/0] via 172.16.0.1, eth3, weight 1, 00:28:33
B>* 0.0.0.0/0 [20/0] via 172.16.0.1, eth3, weight 1, 00:28:33
C>* 10.0.0.0/31 is directly connected, eth1, weight 1, 00:36:02
L>* 10.0.0.0/32 is directly connected, eth1, weight 1, 00:36:02
C>* 10.0.0.2/31 is directly connected, eth2, weight 1, 00:36:02
L>* 10.0.0.2/32 is directly connected, eth2, weight 1, 00:36:02
O>* 10.0.0.4/31 [110/20] via 10.0.0.1, eth1, weight 1, 00:35:14
O>* 10.0.0.6/31 [110/20] via 10.0.0.3, eth2, weight 1, 00:34:52
C>* 10.255.0.11/32 is directly connected, lo, weight 1, 00:36:02
O>* 10.255.0.21/32 [110/20] via 10.0.0.1, eth1, weight 1, 00:35:14
O>* 10.255.0.22/32 [110/20] via 10.0.0.3, eth2, weight 1, 00:34:52
C>* 172.16.0.0/31 is directly connected, eth3, weight 1, 00:36:02
L>* 172.16.0.0/32 is directly connected, eth3, weight 1, 00:36:02
B>* 192.168.1.0/24 [20/0] via 10.255.0.21, eth1, weight 1, 00:35:01
B>* 192.168.2.0/24 [20/0] via 10.255.0.22, eth2, weight 1, 00:34:41
```

## STDERR

```
```

## Notes

Key routes to verify:
- `B>* 0.0.0.0/0` — default route learned from edge1 via eBGP
- `O>* 10.255.0.21/32` — leaf1 loopback learned via OSPF (required for iBGP session)
- `O>* 10.255.0.22/32` — leaf2 loopback learned via OSPF
- `B>* 192.168.1.0/24` — leaf1 host subnet via iBGP (next-hop is leaf1 loopback, resolved via OSPF)
- `B>* 192.168.2.0/24` — leaf2 host subnet via iBGP
