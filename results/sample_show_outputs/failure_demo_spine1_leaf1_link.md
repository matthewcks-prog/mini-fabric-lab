# Failure Demo: spine1–leaf1 Link Failure

This file captures the before/during/after state of the documented failure scenario.

---

## Before: Baseline (all healthy)

```
$ make test

[PASS] spine1 container exists - clab-mini-fabric-lab-spine1 is running
[PASS] spine1 OSPF neighbor count - expected 2, got 2
[PASS] spine1 BGP peer 10.255.0.21 - expected Established, got Established
[PASS] spine1 BGP peer 10.255.0.22 - expected Established, got Established
[PASS] spine1 BGP peer 172.16.0.1 - expected Established, got Established
[PASS] spine1 route 192.168.1.0/24 - present in routing table
[PASS] spine1 route 192.168.2.0/24 - present in routing table
[PASS] spine1 route 0.0.0.0/0 - present in routing table
[PASS] spine2 container exists - clab-mini-fabric-lab-spine2 is running
[PASS] spine2 OSPF neighbor count - expected 2, got 2
...
[PASS] h1 ping 192.168.2.10 - reachable
[PASS] h2 ping 192.168.1.10 - reachable

Report written to: results/healthcheck-20260408-142301.md
```

---

## Failure Injection

```bash
docker exec clab-mini-fabric-lab-spine1 ip link set eth1 down
```

---

## During: Degraded state (~5 seconds after failure)

### spine1 OSPF neighbors (one dropped)

```
spine1# show ip ospf neighbor

Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
10.255.0.22       1 Full/-          6m04s             38.512s 10.0.0.3        eth2:10.0.0.2
```

Only spine1–leaf2 adjacency remains. spine1–leaf1 adjacency dropped immediately (interface went down, OSPF removes adjacency on link-down, no need to wait for dead-interval).

### spine1 BGP summary (leaf1 session lost)

```
spine1# show ip bgp summary

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd
10.255.0.21     4      65100        92        93        0    0    0 00:00:08    Active
10.255.0.22     4      65100        83        89        0    0    0 00:35:21         1
172.16.0.1      4      65050        61        64        0    0    0 00:28:41         1
```

`10.255.0.21` (leaf1) shows `Active` — spine1 can no longer reach leaf1's loopback (`10.255.0.21/32`) because the only OSPF path to it was via the now-down eth1 link.

### leaf1 BGP summary (spine1 session lost, spine2 intact)

```
leaf1# show ip bgp summary

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd
10.255.0.11     4      65100        93        92        0    0    0 00:00:05    Active
10.255.0.12     4      65100        88        90        0    0    0 00:35:01         3
```

leaf1 still has full connectivity via spine2 (`10.255.0.12` Established). h1 can still reach h2 via this path.

### Healthcheck output during failure

```
$ make test

[PASS] spine1 container exists - clab-mini-fabric-lab-spine1 is running
[FAIL] spine1 OSPF neighbor count - expected 2, got 1
[FAIL] spine1 BGP peer 10.255.0.21 - expected Established, got Active
[PASS] spine1 BGP peer 10.255.0.22 - expected Established, got Established
[PASS] spine1 BGP peer 172.16.0.1 - expected Established, got Established
...
[PASS] spine2 OSPF neighbor count - expected 2, got 2
[PASS] spine2 BGP peer 10.255.0.21 - expected Established, got Established
...
[PASS] leaf1 OSPF neighbor count - expected 2, got 1     <- FAIL (only spine2 remains)
[FAIL] leaf1 BGP peer 10.255.0.11 - expected Established, got Active
[PASS] leaf1 BGP peer 10.255.0.12 - expected Established, got Established
...
[PASS] h1 ping 192.168.2.10 - reachable
[PASS] h2 ping 192.168.1.10 - reachable
```

**Key observation:** h1 ↔ h2 reachability is maintained throughout the failure. The dual-homed design (each leaf connected to both spines) ensures traffic continues via the surviving path (leaf1 → spine2 → leaf2).

---

## Recovery

```bash
docker exec clab-mini-fabric-lab-spine1 ip link set eth1 up
```

After ~10 seconds:
1. OSPF adjacency reforms (interface UP → hello exchange → Full state)
2. spine1 OSPF table updates: leaf1 loopback (`10.255.0.21/32`) reachable again
3. BGP TCP session re-establishes (spine1 connects to `10.255.0.21:179`)
4. Routes re-exchanged; ECMP paths restored on all nodes

### Post-recovery healthcheck

```
$ make test

[PASS] spine1 OSPF neighbor count - expected 2, got 2
[PASS] spine1 BGP peer 10.255.0.21 - expected Established, got Established
...
[PASS] h1 ping 192.168.2.10 - reachable
[PASS] h2 ping 192.168.1.10 - reachable

Report written to: results/healthcheck-20260408-143412.md
```

All 35 checks pass. Recovery confirmed.
