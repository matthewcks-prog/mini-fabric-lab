# spine1: show ip bgp summary

- Return code: 0

## STDOUT

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 10.255.0.11, local AS number 65100 VRF default vrf-id 0
BGP table version 8
RIB entries 5, using 960 bytes of memory
Peers 3, using 2176 bytes of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.255.0.21     4      65100        87        92        0    0    0 00:35:14            1        3 N/A
10.255.0.22     4      65100        83        89        0    0    0 00:34:52            1        3 N/A
172.16.0.1      4      65050        61        64        0    0    0 00:28:33            1        2 N/A

Total number of neighbors 3
```

## STDERR

```
```

## Notes

Three BGP peers shown:
- `10.255.0.21` (leaf1) — iBGP RR client; receiving 1 prefix (192.168.1.0/24), sending 3 (192.168.2.0/24, 0.0.0.0/0, and 192.168.1.0/24 reflected back)
- `10.255.0.22` (leaf2) — iBGP RR client; symmetric to leaf1
- `172.16.0.1` (edge1) — eBGP; receiving 1 prefix (default route), sending 2 (host subnets, filtered by TO-EDGE-OUT)

All sessions in `Established` state (numeric value in `State/PfxRcd`).
