# leaf1: show ip route

- Return code: 0

## STDOUT

```
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIP, O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

B>* 0.0.0.0/0 [200/0] via 10.255.0.11, eth1, weight 1, 00:28:15
              [200/0] via 10.255.0.12, eth2, weight 1, 00:28:15
C>* 10.0.0.0/31 is directly connected, eth1, weight 1, 00:36:02
L>* 10.0.0.1/32 is directly connected, eth1, weight 1, 00:36:02
C>* 10.0.0.4/31 is directly connected, eth2, weight 1, 00:36:02
L>* 10.0.0.5/32 is directly connected, eth2, weight 1, 00:36:02
O>* 10.0.0.2/31 [110/20] via 10.0.0.0, eth1, weight 1, 00:35:14
O>* 10.0.0.6/31 [110/20] via 10.0.0.4, eth2, weight 1, 00:34:58
C>* 10.255.0.21/32 is directly connected, lo, weight 1, 00:36:02
O>* 10.255.0.11/32 [110/20] via 10.0.0.0, eth1, weight 1, 00:35:14
O>* 10.255.0.12/32 [110/20] via 10.0.0.4, eth2, weight 1, 00:34:58
O>* 10.255.0.22/32 [110/20] via 10.0.0.0, eth1, weight 1, 00:35:14
C>* 192.168.1.0/24 is directly connected, eth3, weight 1, 00:36:02
L>* 192.168.1.1/32 is directly connected, eth3, weight 1, 00:36:02
B>* 192.168.2.0/24 [200/0] via 10.255.0.11, eth1, weight 1, 00:34:41
                   [200/0] via 10.255.0.12, eth2, weight 1, 00:34:41
```

## STDERR

```
```

## Notes

Key observations for leaf1:
- `B>* 0.0.0.0/0` via both spine loopbacks — ECMP default route; traffic uses both spines (load-balances)
- `O>* 10.255.0.11/32` and `O>* 10.255.0.12/32` — spine loopbacks reachable via OSPF (required for iBGP sessions to form)
- `B>* 192.168.2.0/24` via both spines — leaf2's host subnet, received via iBGP, two equal-cost paths (one per spine RR)
- iBGP routes show `[200/0]` — administrative distance 200 (iBGP), metric 0 (no MED set)
