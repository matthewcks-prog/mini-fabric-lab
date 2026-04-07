# h2: end-to-end connectivity to h1

## ping h1 (192.168.1.10)

```
$ docker exec clab-mini-fabric-lab-h2 ping -c5 192.168.1.10

PING 192.168.1.10 (192.168.1.10) 56(84) bytes of data.
64 bytes from 192.168.1.10: icmp_seq=1 ttl=61 time=0.428 ms
64 bytes from 192.168.1.10: icmp_seq=2 ttl=61 time=0.404 ms
64 bytes from 192.168.1.10: icmp_seq=3 ttl=61 time=0.411 ms
64 bytes from 192.168.1.10: icmp_seq=4 ttl=61 time=0.419 ms
64 bytes from 192.168.1.10: icmp_seq=5 ttl=61 time=0.407 ms

--- 192.168.1.10 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4093ms
rtt min/avg/max/mdev = 0.404/0.414/0.428/0.009 ms
```

**Result:** 0% packet loss. Bidirectional reachability confirmed.

## traceroute h1 (192.168.1.10)

```
$ docker exec clab-mini-fabric-lab-h2 traceroute -n 192.168.1.10

traceroute to 192.168.1.10 (192.168.1.10), 30 hops max, 46 byte packets
 1  192.168.2.1   0.331 ms  0.309 ms  0.298 ms    <- leaf2 eth3 (h2's default gateway)
 2  10.255.0.12   0.369 ms  0.351 ms  0.363 ms    <- spine2 loopback
 3  192.168.1.1   0.390 ms  0.381 ms  0.395 ms    <- leaf1 eth3 (h1's gateway)
 4  192.168.1.10  0.408 ms  0.399 ms  0.412 ms    <- h1
```

**Path confirmed:** h2 → leaf2 → spine2 → leaf1 → h1.

Traffic from h2 naturally hashes to spine2, while traffic from h1 (in the ping_and_traceroute.md) went via spine1 — both spines are actively carrying traffic (ECMP working at the leaf level).

## h2 ip addr / ip route

```
$ docker exec clab-mini-fabric-lab-h2 ip addr show eth1

3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether aa:c1:ab:78:90:ab brd ff:ff:ff:ff:ff:ff
    inet 192.168.2.10/24 brd 192.168.2.255 scope global eth1

$ docker exec clab-mini-fabric-lab-h2 ip route show

default via 192.168.2.1 dev eth1
192.168.2.0/24 dev eth1 proto kernel scope link src 192.168.2.10
```
