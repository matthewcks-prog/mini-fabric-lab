# Design Notes — Mini Fabric Lab

## Purpose

This document explains the architecture decisions behind every layer of the lab: why each protocol was chosen, how the addressing is structured, where the policy sits, and what the automation does. It is written to be read alongside the configs in `configs/frr/` and the topology definition in `clab/topology.clab.yml`.

---

## Goals

| Goal | How it is met |
|---|---|
| Demonstrate OSPF and BGP fundamentals end-to-end | OSPF underlay + iBGP overlay + eBGP edge, all running simultaneously |
| Show a real scaling pattern (not just point-to-point BGP) | Route reflectors on spines eliminate the full-mesh requirement |
| Enforce routing policy at the boundary | Prefix-list + route-map controls what enters and leaves the fabric |
| Make the lab reproducible and reviewable | Topology-as-code (`topology.clab.yml`), configs-as-code (`frr.conf` per node) |
| Prove correctness automatically | `healthcheck.py` validates neighbor state, route presence, and data-plane reachability |

---

## Topology Overview

```
              edge1  AS 65050
             /      \
       eBGP /        \ eBGP
           /          \
      spine1 -------- spine2    AS 65100  (iBGP RR mesh)
       / \              / \
      /   \            /   \
  leaf1   leaf2    leaf1   leaf2          (same nodes, dual-homed)
    |                  |
   h1               h2
```

More precisely:

- **spine1** and **spine2** are both Route Reflectors (RR) for AS 65100
- **leaf1** and **leaf2** are RR clients; they peer only with the two spines
- **edge1** (AS 65050) peers with both spines via eBGP — dual-homed for redundancy
- **h1** and **h2** are plain Linux containers that validate the data plane

---

## IP Addressing

### Loopbacks (stable BGP peer addresses)

| Node   | Loopback        |
|--------|-----------------|
| spine1 | 10.255.0.11/32  |
| spine2 | 10.255.0.12/32  |
| leaf1  | 10.255.0.21/32  |
| leaf2  | 10.255.0.22/32  |
| edge1  | 10.255.0.31/32  |

Loopbacks are advertised into OSPF so that iBGP sessions can source from them. This is the standard pattern: loopbacks are stable (they do not go down when a physical link fails), making them ideal BGP session endpoints.

### Fabric point-to-point links (10.0.0.0/24, /31 subnets)

| Link              | Subnet        | spine side   | leaf side    |
|-------------------|---------------|--------------|--------------|
| spine1 ↔ leaf1   | 10.0.0.0/31   | eth1: .0     | eth1: .1     |
| spine1 ↔ leaf2   | 10.0.0.2/31   | eth2: .2     | eth1: .3     |
| spine2 ↔ leaf1   | 10.0.0.4/31   | eth1: .4     | eth2: .5     |
| spine2 ↔ leaf2   | 10.0.0.6/31   | eth2: .6     | eth2: .7     |

`/31` subnets are used on point-to-point links (RFC 3021). This eliminates the broadcast and network addresses and is standard practice on fabric links.

### Edge uplinks (172.16.0.0/30)

| Link              | Subnet         | spine side   | edge1 side   |
|-------------------|----------------|--------------|--------------|
| spine1 ↔ edge1   | 172.16.0.0/31  | eth3: .0     | eth1: .1     |
| spine2 ↔ edge1   | 172.16.0.2/31  | eth3: .2     | eth2: .3     |

A separate prefix block is used for the edge uplinks to keep the fabric addressing (`10.0.0.0/24`) visually distinct from the transit links.

### Host subnets

| Host | Subnet           | Host IP        | Default GW    |
|------|------------------|----------------|---------------|
| h1   | 192.168.1.0/24   | 192.168.1.10   | 192.168.1.1 (leaf1 eth3) |
| h2   | 192.168.2.0/24   | 192.168.2.10   | 192.168.2.1 (leaf2 eth3) |

---

## Layer 1 — Containerlab Topology Definition

`clab/topology.clab.yml` defines every node and every link. Nodes use the official FRR image (`quay.io/frrouting/frr:10.5.1`); hosts use `ghcr.io/hellt/network-multitool` (a lightweight Linux image with common network utilities).

FRR configs are bind-mounted at startup:

```yaml
binds:
  - ../configs/frr/spine1/daemons:/etc/frr/daemons
  - ../configs/frr/spine1/frr.conf:/etc/frr/frr.conf
  - ../configs/frr/spine1/vtysh.conf:/etc/frr/vtysh.conf
```

This means **changing a config file and redeploying is the only way to change router state** — there is no ad-hoc CLI state that diverges from version control. That is the "configs-as-code" property.

Links are declared as endpoint pairs (`spine1:eth1` ↔ `leaf1:eth1`). Containerlab creates Linux veth pairs and places them in the correct network namespace for each container. No manual `ip link` or `brctl` required.

---

## Layer 2/3 — OSPF Underlay

### Why OSPF for the underlay

OSPF is an IGP well-suited to a small, stable fabric:

- **Zero pre-configuration for neighbor discovery** on point-to-point links — as long as the network is in the correct `router ospf` stanza, adjacency forms automatically.
- **Fast convergence** using dead-interval timers; the fabric is small enough that OSPF reconverges in under 10 seconds on a link failure.
- **Distributes loopbacks as /32 host routes** — exactly what iBGP needs as stable next-hops.

### OSPF design choices

| Choice | Detail |
|---|---|
| Single area (area 0) | Five routers do not warrant hierarchy; area 0 everywhere keeps the design simple |
| `passive-interface default` | All interfaces are passive by default; OSPF is explicitly enabled only on fabric links using `no passive-interface` |
| Loopbacks passive | Loopbacks are included in OSPF via `network` stanza but remain passive (no hellos sent on lo); they are just redistributed as /32 prefixes |
| Point-to-point network type | `ip ospf network point-to-point` on all fabric links — no DR/BDR election overhead on /31 links, faster adjacency formation |
| Edge links excluded from OSPF | The 172.16.0.x links are not announced into OSPF; only loopbacks and fabric links are. This keeps the routing domain clean and prevents internal nodes from learning about external link topology |

### What OSPF carries

After convergence, every router in AS 65100 has OSPF routes to:

- All /31 fabric link subnets (10.0.0.0/24 block)
- All loopbacks (10.255.0.x/32)

It does **not** carry host subnets (`192.168.x.0/24`) or the default route — those are BGP's job.

---

## Layer 3 — BGP Overlay

### iBGP design: Route Reflectors

**Why iBGP for the overlay?**

BGP is the standard protocol for distributing reachability information across a fabric because it:

- Scales to very large prefix counts
- Supports fine-grained policy (route-maps, prefix-lists, communities, local-pref)
- Can be controlled independently of the underlay IGP

**Why route reflectors instead of full-mesh?**

Full-mesh iBGP requires `n(n-1)/2` sessions. With 4 iBGP speakers (spine1, spine2, leaf1, leaf2), that is 6 sessions. With 100 leaves, it would be 4950. Route reflectors eliminate this:

- Leaves only establish sessions to spine1 and spine2 (2 sessions each)
- Spines reflect routes learned from one client to all other clients and to eBGP peers
- Adding a new leaf requires only 2 new sessions, not n−1

The spine placement for RRs is natural: spines already have physical connectivity to every leaf, so they are the correct convergence point for routing information.

**Configuration pattern on spines:**

```
router bgp 65100
  neighbor 10.255.0.21 remote-as 65100
  neighbor 10.255.0.21 update-source lo
  neighbor 10.255.0.22 remote-as 65100
  neighbor 10.255.0.22 update-source lo
  address-family ipv4 unicast
    neighbor 10.255.0.21 route-reflector-client
    neighbor 10.255.0.22 route-reflector-client
    neighbor 10.255.0.21 next-hop-self
    neighbor 10.255.0.22 next-hop-self
```

`update-source lo` forces BGP to use the loopback as the TCP source, which requires OSPF to carry the loopback routes first. This is correct dependency ordering: OSPF up → loopbacks reachable → iBGP sessions establish.

### Why `next-hop-self` is non-negotiable

When spine1 reflects a route originally advertised by edge1 (with BGP next-hop `172.16.0.1`) to leaf1, the next-hop is still `172.16.0.1`. Leaf1 has no OSPF route to `172.16.0.1` — the edge links are deliberately excluded from OSPF.

`next-hop-self` on the spine causes it to rewrite the BGP next-hop to its own loopback (`10.255.0.11`) before sending the update to leaves. Leaf1 *does* have an OSPF route to `10.255.0.11`, so the route becomes usable.

Without `next-hop-self`: routes present in `show ip bgp`, but `show ip route` shows them as unreachable (next-hop not in FIB). Pings fail.

### eBGP design: Edge router

**edge1** is in a separate AS (65050) and represents an upstream or transit provider. It:

1. Peers with both spines (dual-homed for redundancy)
2. Originates a default route (`0.0.0.0/0`) toward the fabric
3. Receives the internal host subnets from the fabric

**Default route origination method:**

```
ip route 0.0.0.0/0 Null0          ! static black-hole to make default "present"
neighbor 172.16.0.0 default-originate
neighbor 172.16.0.2 default-originate
```

The Null0 static is a conditional trigger: FRR will originate the default via `default-originate` only if the default route exists in the RIB. The Null0 ensures this condition is always met without needing a real upstream connection. This is the production-safe pattern — it does not rely on a `network 0.0.0.0/0` statement that could silently disappear if the route goes missing.

### iBGP between spines

Spine1 and spine2 are both RRs. In standard BGP, an RR does not re-reflect routes received from another RR to prevent loops. The two-spine design sidesteps this: each spine learns leaf routes directly from leaves (as their RR), and eBGP routes from edge1. There is no strict need for spine1↔spine2 iBGP in this topology, but if added it would use the standard `no route-reflector-client` peer (non-client peer between RRs).

---

## Routing Policy

Policy is applied on the spines at the eBGP boundary, controlling what enters and exits the fabric.

### Inbound from edge1 (`FROM-EDGE-IN`)

```
ip prefix-list DEFAULT-ONLY seq 5 permit 0.0.0.0/0
route-map FROM-EDGE-IN permit 10
  match ip address prefix-list DEFAULT-ONLY
```

**Permits only `0.0.0.0/0`.** Any other routes edge1 might advertise (e.g., more specific prefixes, RFC 1918 space, or leaked internal routes) are silently dropped. This is a standard "default-only" customer policy.

### Outbound to edge1 (`TO-EDGE-OUT`)

```
ip prefix-list FABRIC-OUT seq 5 permit 192.168.1.0/24
ip prefix-list FABRIC-OUT seq 10 permit 192.168.2.0/24
route-map TO-EDGE-OUT permit 10
  match ip address prefix-list FABRIC-OUT
```

**Permits only the two host subnets.** Infrastructure prefixes (loopbacks, fabric /31 links) are never advertised externally. This limits the attack surface and prevents the edge router from learning about internal topology.

### Why implicit deny at the end of route-maps

Both route-maps end after a single `permit` sequence. FRR (and standard BGP practice) appends an implicit `deny all` at the end of any route-map. This means anything not explicitly permitted is denied — a safe default that requires you to explicitly whitelist what is allowed.

---

## Host Configuration

Hosts are plain Linux containers. Their startup scripts (`configs/hosts/h1.sh`, `configs/hosts/h2.sh`) do exactly three things:

```sh
ip link set eth1 up
ip addr replace 192.168.1.10/24 dev eth1
ip route replace default via 192.168.1.1 dev eth1
```

1. Bring the interface up
2. Assign the host IP
3. Set a default route pointing to the leaf's gateway IP

Using `ip addr replace` and `ip route replace` instead of `add` makes the script idempotent — safe to re-run without errors if the address or route already exists.

---

## Automation Design

### `healthcheck.py`

The health-check is designed to be **deterministic and declarative**: expected state is defined in `automation/expected_state.yml`, and the script asserts reality matches it.

**Flow:**

1. Load `expected_state.yml`
2. For each router: check container is running → check OSPF neighbor count → check each BGP peer is Established → check each required prefix is in the routing table
3. For each host: ping the cross-fabric target
4. Write a timestamped Markdown report to `results/`
5. Exit non-zero if any check failed

**Why JSON output from FRR:**

`show ip bgp summary json` returns structured JSON that is stable across FRR versions and easy to parse without fragile regex. The script falls back to regex-based parsing for OSPF neighbor output (which does not always have a JSON variant depending on FRR build).

**Why `subprocess` + `docker exec`:**

The health-check runs on the host and reaches into containers via `docker exec`. This is intentional — it models how a real network automation tool would query devices externally, rather than requiring the script to run inside a container.

### `collect_evidence.py`

The evidence collector runs the same commands as the health-check but saves raw output files to timestamped directories under `results/`. This produces the recruiter-friendly artifacts that prove the lab worked, without embedding huge logs in the README.

### `expected_state.yml`

The declarative spec for what "correct" looks like:

```yaml
routers:
  spine1:
    ospf_neighbors: 2
    bgp_neighbors:
      10.255.0.21: Established
      10.255.0.22: Established
      172.16.0.1: Established
    must_have_routes:
      - 192.168.1.0/24
      - 192.168.2.0/24
      - 0.0.0.0/0
```

This file is the single source of truth for what the health-check validates. Changing this file is the mechanism for updating what "pass" means — useful for testing failure scenarios (e.g., temporarily removing a neighbor expectation to validate degraded-mode behavior).

---

## Topology-as-Code Properties

| Property | Mechanism |
|---|---|
| Reproducible bring-up | `clab deploy -t topology.clab.yml` (or `make deploy`) always produces the same topology |
| Idempotent | Re-running deploy on an existing lab is safe; containerlab handles node and link state |
| Version-controlled | All YAML and FRR config files are plain text; git diff shows exactly what changed |
| One-command teardown | `make destroy` removes all containers and virtual links, leaving no orphaned state |

---

## Scaling Considerations

This lab is explicitly small (5 routers, 2 hosts). The design choices deliberately mirror how larger fabrics are built:

| Lab pattern | Production equivalent |
|---|---|
| Loopbacks as BGP peer addresses | Standard in any multi-hop iBGP design |
| Route reflectors on spines | Scales to thousands of leaves without iBGP full-mesh |
| `next-hop-self` on RRs | Required in any iBGP design where the IGP does not carry eBGP next-hops |
| Prefix-list policy at the edge | Standard BGP security baseline |
| OSPF passive-interface default | Prevents hellos leaking onto host-facing interfaces |

Adding a third leaf would require: a new node in `topology.clab.yml`, a new `configs/frr/leaf3/` directory, adding `leaf3` to both spines' BGP neighbor config, and adding leaf3 to `expected_state.yml`. The structure is designed to make this obvious and low-risk.

---

## What Would Change on Real Hardware

This section is included to be honest about the lab's scope and limitations:

| Aspect | Lab (containerized) | Hardware |
|---|---|---|
| Forwarding plane | Linux kernel IP forwarding | Dedicated ASIC (Broadcom Trident, Mellanox Spectrum, etc.) |
| Interface types | Linux veth pairs | Physical copper/fiber + optics |
| Link failure detection | OSPF dead-interval (default 40 s) or `ip link down` | BFD sub-second, plus hardware link-down signaling |
| MTU | Inherited from host kernel (typically 1500) | Configurable per port, jumbo frames common in data centers |
| QoS/traffic shaping | None | Hardware queues, DSCP marking, scheduling |
| Convergence timers | Software timers (slower) | BFD + hardware notifications (sub-second) |
| Scale | 5 nodes trivial for a laptop | Production fabrics: hundreds of leaves, millions of routes |
| Vendor CLI | FRR (open source) | Cisco NX-OS, Arista EOS, Juniper JunOS, Cumulus Linux, etc. |

The control-plane behavior (protocol state machines, route selection, policy application) is functionally equivalent between FRR in a container and a hardware router running the same protocols. The differences are in the forwarding plane and operational tooling.
