# Troubleshooting Notes — Mini Fabric Lab

## Methodology

Always work bottom-up through the layers. Skipping layers wastes time; a BGP session will never establish if the underlying IP connectivity is broken.

```
Layer 5 — Data plane     ping, traceroute, tcpdump
Layer 4 — Route presence show ip route, show bgp ipv4 unicast
Layer 3b — BGP           show ip bgp summary, show ip bgp neighbor
Layer 3a — OSPF          show ip ospf neighbor, show ip route ospf
Layer 2/1 — Links        ip link, ip addr, ip route (Linux)
Layer 0 — Containers     docker ps, docker inspect
```

**Rule:** Don't assume a higher layer is broken until the layer below is confirmed working.

---

## Layer 0 — Container / Lab Health

### Check all containers are running

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected: all 7 containers (`clab-mini-fabric-lab-spine1`, `spine2`, `leaf1`, `leaf2`, `edge1`, `h1`, `h2`) show `Up`.

### Container not listed or shows `Exited`

```bash
docker inspect clab-mini-fabric-lab-spine1 | grep -A5 '"State"'
docker logs clab-mini-fabric-lab-spine1
```

**Common causes:**
- FRR config syntax error — `docker logs` will show `frr.conf: line X: error`
- Missing bind-mount file — container exits immediately if `/etc/frr/frr.conf` doesn't exist
- Port/name conflict from a previous lab run — run `make destroy` then `make deploy`

### Exec into a container

```bash
docker exec -it clab-mini-fabric-lab-spine1 bash        # shell
docker exec -it clab-mini-fabric-lab-spine1 vtysh       # FRR CLI
```

---

## Layer 1 — Links and Addressing (Linux)

Run these **inside** the container (via `docker exec -it <container> bash`).

### Verify interfaces are up and addressed

```bash
ip link show          # all interfaces; look for UP flag
ip addr show          # check IP on each interface
```

For spine1, expected output (abbreviated):

```
1: lo: <LOOPBACK,UP> ...
    inet 10.255.0.11/32 scope host lo
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 10.0.0.0/31 brd 0.0.0.1 scope global eth1
4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 10.0.0.2/31 brd 0.0.0.3 scope global eth2
5: eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 172.16.0.0/31 brd 172.16.0.1 scope global eth3
```

### Issue: interface is DOWN

```bash
ip link set eth1 up   # bring it up manually (temporary fix; check frr.conf for permanent fix)
```

### Verify direct-connected reachability

From spine1, ping the directly connected leaf1 address:

```bash
ping -c3 10.0.0.1     # spine1 eth1 → leaf1 eth1
```

If this fails, there is a Layer 1/2 issue (veth pair not created, or containerlab link not fully up). Redeploy:

```bash
make destroy && make deploy
```

### Check Linux routing table

```bash
ip route show
```

On a host container (h1), you must see a default route:

```
default via 192.168.1.1 dev eth1
192.168.1.0/24 dev eth1 proto kernel scope link src 192.168.1.10
```

If the default route is missing, the host startup script (`h1.sh`) did not run or failed. Check:

```bash
docker logs clab-mini-fabric-lab-h1
```

---

## Layer 3a — OSPF

### Check OSPF neighbor state

From inside a router container (`vtysh`):

```
show ip ospf neighbor
```

For spine1, expected (both leaves in `Full` state):

```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
10.255.0.21       1 Full/-          5m12s             34.123s 10.0.0.1        eth1:10.0.0.0
10.255.0.22       1 Full/-          5m09s             31.456s 10.0.0.3        eth2:10.0.0.2
```

### Issue: No neighbors listed (table empty)

**Checklist:**
1. Is the interface up? (`ip link show eth1` — must show `UP,LOWER_UP`)
2. Is the network statement correct? (`show running-config` → `router ospf` section)
3. Is the interface in the correct network? spine1 eth1 is `10.0.0.0/31`; the `network 10.0.0.0/31 area 0` statement must match.
4. Is the interface passive? `passive-interface default` makes everything passive. Confirm `no passive-interface eth1` exists in the OSPF config.

Quick verification:

```
show ip ospf interface eth1
```

Look for `OSPF enabled` and `Point-to-Point` network type. If it says `Passive`, fix the `no passive-interface` config.

### Issue: Neighbor stuck in `INIT` or `2-Way`

- **INIT**: spine1 sees hellos from the neighbor but the neighbor does not see spine1's hellos (one-way hello). Check the veth is truly bidirectional. Redeploy if needed.
- **2-Way**: Seen on broadcast interfaces only; should not occur here because all fabric interfaces are configured as `point-to-point`.

### Issue: Neighbor stuck in `EXSTART` or `EXCHANGE`

Usually a **MTU mismatch**. In a container environment MTU is typically 1500 everywhere, so this is rare. If it appears:

```
show ip ospf interface eth1   # check mtu
```

Add `ip ospf mtu-ignore` to the interface in `frr.conf` as a workaround (documents the issue; investigate underlying MTU later).

### Verify OSPF routes are in the routing table

```
show ip route ospf
```

On spine1, expected routes (abbreviated):

```
O   10.0.0.4/31 [110/20] via 10.0.0.1, eth1 (leaf1→spine2 link, learned via leaf1)
O   10.0.0.6/31 [110/20] via 10.0.0.3, eth2 (leaf2→spine2 link, learned via leaf2)
O   10.255.0.21/32 [110/20] via 10.0.0.1, eth1 (leaf1 loopback)
O   10.255.0.22/32 [110/20] via 10.0.0.3, eth2 (leaf2 loopback)
```

Missing loopback routes → iBGP sessions using loopbacks will not form.

---

## Layer 3b — BGP

### Check BGP session state

```
show ip bgp summary
```

On spine1, expected:

```
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd
10.255.0.21     4      65100        87        92        0    0    0 00:35:14            1
10.255.0.22     4      65100        83        89        0    0    0 00:34:52            1
172.16.0.1      4      65050        61        64        0    0    0 00:28:33            1
```

`State/PfxRcd` showing a number (not `Active`, `Idle`, or `Connect`) means Established. A state word means the session has not completed.

### Issue: BGP session in `Active`

Session is trying to connect but not succeeding. Most common causes:

1. **OSPF loopback route missing** — run `show ip route 10.255.0.21/32` on spine1. If not present, OSPF is not distributing leaf1's loopback. Fix OSPF first.
2. **Wrong `update-source`** — the `neighbor 10.255.0.21 update-source lo` config must be present. Without it, spine1 tries to source the TCP session from the eth1 address (`10.0.0.0`), but leaf1 has the BGP peer configured expecting `10.255.0.11` (the loopback). BGP TCP SYN arrives from the wrong address and is rejected.
3. **AS number mismatch** — `neighbor 10.255.0.21 remote-as 65100` must match the `bgp router-id` AS on leaf1's side.

### Issue: BGP session `Idle`

BGP is not even trying to connect. Usually means:
- The FRR BGP daemon is not running (`show ip bgp` returns an error) — check `daemons` file for `bgpd=yes`
- A hard reset was issued (`clear ip bgp * hard`) and holddown is active

### Issue: BGP Established but neighbor shows 0 prefixes received

Session is up, but no routes are being exchanged. This is one of the most common BGP gotchas.

**Checklist:**
1. **Does the advertising node have the prefix in its RIB?**
   On leaf1: `show ip route 192.168.1.0/24` — must show a connected route. If eth3 is down, the prefix is not in the RIB and the `network 192.168.1.0/24` statement will not originate it.

2. **Is a route-map filtering everything out?**
   On the spine, inbound from edge: `FROM-EDGE-IN` permits only `0.0.0.0/0`. Anything else from edge is denied. This is correct behavior. Verify edge is only advertising the default:
   ```
   show ip bgp neighbors 172.16.0.1 received-routes
   ```

3. **Is there a route-map that denies outbound?**
   On the spine, outbound to edge: `TO-EDGE-OUT` permits only `192.168.1.0/24` and `192.168.2.0/24`. If a leaf's subnet is not in this list, it will not be advertised to edge. Check the prefix-list:
   ```
   show ip prefix-list FABRIC-OUT
   ```

4. **Is the next-hop resolvable?**
   On a leaf: `show ip bgp 0.0.0.0/0` — check the `Next Hop` field. It should be a spine loopback (e.g., `10.255.0.11`). If it shows an edge link address (`172.16.0.1`), `next-hop-self` is missing on the spine.

### Check detailed BGP neighbor information

```
show ip bgp neighbors 10.255.0.21
```

This shows the full neighbor state, including:
- `BGP state = Established`
- `Hold time`, `Keepalive interval`
- `Route Reflector Client` — confirms RR-client relationship
- `Update group` and `Subgroup` — useful for debugging why updates are or are not being sent

### Check BGP RIB

```
show bgp ipv4 unicast          # full BGP table
show ip bgp 192.168.2.0/24     # specific prefix — shows all paths and best-path selection
```

On leaf1, expected for `192.168.2.0/24`:

```
BGP routing table entry for 192.168.2.0/24
Paths: (2 available, best #1, table default)
  Advertised to non peer-group peers:
  10.255.0.11 10.255.0.12
  65100
    10.255.0.11 from 10.255.0.11 (10.255.0.11)    <- spine1 RR reflected
      Origin IGP, localpref 100, valid, internal, best
  65100
    10.255.0.12 from 10.255.0.12 (10.255.0.12)    <- spine2 RR reflected
      Origin IGP, localpref 100, valid, internal
```

Two paths (one via each spine) means dual-path redundancy is working.

### Soft reset without tearing down sessions

```
clear ip bgp 10.255.0.21 soft   # soft reset — re-sends updates without dropping session
clear ip bgp * soft out          # re-send all outbound updates to all neighbors
```

---

## Layer 4 — Route Presence in FIB

A BGP route can be in the BGP RIB but not installed in the FIB (routing table). This happens when the next-hop is not resolvable.

```
show ip route
show ip route 192.168.2.0/24
```

On leaf1, `192.168.2.0/24` should show as `B>*` (BGP best, installed):

```
B>* 192.168.2.0/24 [20/0] via 10.255.0.11, eth1, weight 1, 00:34:12
                   [20/0] via 10.255.0.12, eth2, weight 1, 00:34:12
```

If the route shows as `B  ` (no `>` or `*`), the next-hop is not resolvable. Run:

```
show ip route 10.255.0.11/32     # must be an OSPF route
```

Fix: ensure spine loopback is in OSPF (`network 10.255.0.11/32 area 0` on spine1).

### Check default route on leaves

```
show ip route 0.0.0.0/0
```

Expected on leaf1:

```
B>* 0.0.0.0/0 [20/0] via 10.255.0.11, eth1, weight 1, 00:28:11
              [20/0] via 10.255.0.12, eth2, weight 1, 00:28:11
```

If missing: check edge1 is advertising a default (`show ip bgp neighbors 172.16.0.0 advertised-routes` on edge1), and that the spine's `FROM-EDGE-IN` route-map is permitting it.

---

## Layer 5 — Data Plane (Ping and Traceroute)

### h1 cannot ping h2

Work through the layers first. If routing tables look correct, use traceroute:

```bash
docker exec clab-mini-fabric-lab-h1 traceroute -n 192.168.2.10
```

Expected path: `192.168.1.1` (leaf1) → one of the spine addresses → `192.168.2.1` (leaf2) → `192.168.2.10` (h2).

If traceroute shows `* * *` at a hop, traffic is being dropped there. Use tcpdump to verify:

```bash
# On leaf1, watch for ICMP from h1
docker exec clab-mini-fabric-lab-leaf1 tcpdump -ni eth3 icmp

# On spine1, watch for forwarded ICMP
docker exec clab-mini-fabric-lab-spine1 tcpdump -ni eth1 icmp
```

### Common data-plane failure patterns

| Symptom | Likely cause | Fix |
|---|---|---|
| `h1 ping h2` fails; `h1 ping 192.168.1.1` succeeds | Routing on leaf1 or spine is broken | Check leaf1 has `192.168.2.0/24` in FIB |
| Traffic goes to spine1, does not return | Asymmetric routing or missing return path | Check leaf2 has `192.168.1.0/24` in FIB |
| Ping works h1→h2, fails h2→h1 | One-way routing | Check both leaves independently |
| Ping to h2 fails from leaf1 directly | eth3 on leaf2 is down or h2 gateway wrong | Check `ip addr` on h2 and leaf2 eth3 |
| All pings fail after link flap | Routing reconverged but stale ARP or FIB entry | Wait for convergence (up to 15s); re-run `make test` |

### Check IP forwarding is enabled

Linux containers must have IP forwarding enabled for packets to transit (router behavior). FRR containers enable this automatically. Verify:

```bash
docker exec clab-mini-fabric-lab-spine1 sysctl net.ipv4.ip_forward
# Expected: net.ipv4.ip_forward = 1
```

If `0`, traffic arriving on one interface will not be forwarded to another. Set temporarily with:

```bash
docker exec clab-mini-fabric-lab-spine1 sysctl -w net.ipv4.ip_forward=1
```

Permanent fix: add to the FRR container's startup or use a containerlab `exec` stanza in the topology file.

---

## Failure and Recovery Demo: spine1–leaf1 Link Failure

This is the documented failure scenario. Use it to verify the design is resilient.

### Step 1: Baseline — confirm all healthy

```bash
make test     # or: python3 automation/healthcheck.py
```

All checks should pass.

### Step 2: Simulate the failure

```bash
docker exec clab-mini-fabric-lab-spine1 ip link set eth1 down
```

This brings down the veth connecting spine1 (eth1) to leaf1 (eth1).

### Step 3: Observe reconvergence

Within ~5–10 seconds:
- OSPF on spine1 detects the link is down (interface goes down → OSPF removes adjacency immediately for link-down events)
- spine1 OSPF removes the direct route to `10.0.0.1` and to leaf1's loopback
- spine1 BGP session to leaf1 (`10.255.0.21`) goes to `Active` (loopback unreachable via spine1)
- leaf1's OSPF removes spine1 from its neighbor table
- leaf1 still has spine2 OSPF adjacency → leaf1 loopback reachable via spine2 → leaf1 BGP session to spine2 remains Established

### Step 4: Observe the failure in the health-check

```bash
make test
```

Expected FAIL lines:
```
[FAIL] spine1 OSPF neighbor count - expected 2, got 1
[FAIL] spine1 BGP peer 10.255.0.21 - expected Established, got Active
```

Expected PASS lines (resilience confirmed):
```
[PASS] spine2 OSPF neighbor count - expected 2, got 2
[PASS] spine2 BGP peer 10.255.0.21 - expected Established, got Established
[PASS] h1 ping 192.168.2.10 - reachable
[PASS] h2 ping 192.168.1.10 - reachable
```

**h1 can still reach h2** because leaf1's traffic now routes via spine2, which still has full connectivity.

### Step 5: Restore and verify

```bash
docker exec clab-mini-fabric-lab-spine1 ip link set eth1 up
```

Wait ~10–15 seconds for OSPF to reconverge, then:

```bash
make test    # expect all PASS
```

---

## Quick Reference: Commands by Layer

| Layer | Node | Command | What to check |
|---|---|---|---|
| Container | host | `docker ps` | All 7 containers `Up` |
| L1 | any router | `ip link show` | Interfaces `UP,LOWER_UP` |
| L1 | any router | `ip addr show` | Correct IP per interface |
| OSPF | spine/leaf | `show ip ospf neighbor` | Correct count in `Full` state |
| OSPF | spine/leaf | `show ip ospf interface eth1` | Enabled, point-to-point, not passive |
| OSPF routes | spine/leaf | `show ip route ospf` | Loopbacks and fabric links present |
| BGP sessions | spine/leaf/edge | `show ip bgp summary` | All peers Established |
| BGP RIB | spine/leaf | `show bgp ipv4 unicast` | Expected prefixes present |
| BGP next-hop | leaf | `show ip bgp 192.168.2.0/24` | Next-hop is spine loopback, not edge link |
| FIB | leaf | `show ip route 192.168.2.0/24` | Route shows `B>*` (installed) |
| Default route | leaf | `show ip route 0.0.0.0/0` | Present, via spine loopback |
| Edge policy | edge | `show ip bgp neighbors 172.16.0.0 received-routes` | Spine advertises only host subnets |
| Data plane | h1/h2 | `ping -c3 <target>` | 0% packet loss |
| Data plane | h1 | `traceroute -n 192.168.2.10` | Path transits a spine |
| Packet capture | router | `tcpdump -ni eth1 icmp` | Packets arriving and departing |

---

## FRR Daemon Verification

If `vtysh` commands return `% Can not connect to ospfd` or `% Can not connect to bgpd`, the relevant daemon is not running.

Check which daemons are active:

```bash
docker exec clab-mini-fabric-lab-spine1 ps aux | grep frr
```

Expected processes: `zebra`, `ospfd`, `bgpd`, `staticd`.

Check the `daemons` file content:

```bash
docker exec clab-mini-fabric-lab-spine1 cat /etc/frr/daemons
```

Must contain `bgpd=yes`, `ospfd=yes`, `zebra=yes`. If a line reads `=no`, edit `configs/frr/<node>/daemons` and redeploy.

---

## Config Syntax Errors

FRR validates `frr.conf` at startup. Syntax errors cause the daemon to fail to start.

View errors:

```bash
docker logs clab-mini-fabric-lab-spine1 2>&1 | grep -i "error\|warning"
```

Common mistakes:
- Missing `!` comment terminator after interface block (not strictly required but common convention)
- `network` statement in `router ospf` that doesn't match any interface — OSPF will not activate on that interface
- Wrong remote-as in `neighbor` statement — session goes to `Established` briefly then resets with NOTIFICATION

After fixing `frr.conf`:

```bash
make destroy && make deploy
```
