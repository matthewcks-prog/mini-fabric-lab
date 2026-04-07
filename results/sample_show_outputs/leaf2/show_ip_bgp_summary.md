# leaf2: show ip bgp summary

- Return code: 0

## STDOUT

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 10.255.0.22, local AS number 65100 VRF default vrf-id 0
BGP table version 5
RIB entries 3, using 576 bytes of memory
Peers 2, using 1448 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.255.0.11     4      65100        89        84        0    0    0 00:35:02            3        1 N/A
10.255.0.12     4      65100        86        81        0    0    0 00:34:44            3        1 N/A

Total number of neighbors 2
```

## STDERR

```
```

## Notes

leaf2 is symmetric to leaf1: peers only with both spines, originates `192.168.2.0/24` via `network` statement, receives default route and leaf1's subnet via RR reflection from each spine.
