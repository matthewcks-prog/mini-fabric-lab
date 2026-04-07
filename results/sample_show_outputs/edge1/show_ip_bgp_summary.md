# edge1: show ip bgp summary

- Return code: 0

## STDOUT

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 10.255.0.31, local AS number 65050 VRF default vrf-id 0
BGP table version 4
RIB entries 3, using 576 bytes of memory
Peers 2, using 1448 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
172.16.0.0      4      65100        64        61        0    0    0 00:28:33            2        1 N/A
172.16.0.2      4      65100        61        59        0    0    0 00:28:21            2        1 N/A

Total number of neighbors 2
```

## STDERR

```
```

## Notes

edge1 (AS 65050) peers with both spines via eBGP:
- Receiving 2 prefixes from each spine: `192.168.1.0/24` and `192.168.2.0/24` (filtered by `TO-EDGE-OUT` on the spines — only host subnets are advertised outbound)
- Sending 1 prefix to each spine: `0.0.0.0/0` (the default route, originated via `default-originate` triggered by the static `0.0.0.0/0 Null0` in edge1's config)

This confirms the policy is working correctly: edge receives only internal host prefixes; fabric receives only the default route.
