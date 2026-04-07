Healthcheck Report

- Generated: 2026-04-08T14:23:01
- Lab name: `mini-fabric-lab`
- Passed: 34
- Failed: 0

## Check Results

- ✅ **spine1 container exists**: clab-mini-fabric-lab-spine1 is running
- ✅ **spine1 OSPF neighbor count**: expected 2, got 2
- ✅ **spine1 BGP peer 10.255.0.21**: expected Established, got Established
- ✅ **spine1 BGP peer 10.255.0.22**: expected Established, got Established
- ✅ **spine1 BGP peer 172.16.0.1**: expected Established, got Established
- ✅ **spine1 route 192.168.1.0/24**: present in routing table
- ✅ **spine1 route 192.168.2.0/24**: present in routing table
- ✅ **spine1 route 0.0.0.0/0**: present in routing table
- ✅ **spine2 container exists**: clab-mini-fabric-lab-spine2 is running
- ✅ **spine2 OSPF neighbor count**: expected 2, got 2
- ✅ **spine2 BGP peer 10.255.0.21**: expected Established, got Established
- ✅ **spine2 BGP peer 10.255.0.22**: expected Established, got Established
- ✅ **spine2 BGP peer 172.16.0.3**: expected Established, got Established
- ✅ **spine2 route 192.168.1.0/24**: present in routing table
- ✅ **spine2 route 192.168.2.0/24**: present in routing table
- ✅ **spine2 route 0.0.0.0/0**: present in routing table
- ✅ **leaf1 container exists**: clab-mini-fabric-lab-leaf1 is running
- ✅ **leaf1 OSPF neighbor count**: expected 2, got 2
- ✅ **leaf1 BGP peer 10.255.0.11**: expected Established, got Established
- ✅ **leaf1 BGP peer 10.255.0.12**: expected Established, got Established
- ✅ **leaf1 route 192.168.2.0/24**: present in routing table
- ✅ **leaf1 route 0.0.0.0/0**: present in routing table
- ✅ **leaf2 container exists**: clab-mini-fabric-lab-leaf2 is running
- ✅ **leaf2 OSPF neighbor count**: expected 2, got 2
- ✅ **leaf2 BGP peer 10.255.0.11**: expected Established, got Established
- ✅ **leaf2 BGP peer 10.255.0.12**: expected Established, got Established
- ✅ **leaf2 route 192.168.1.0/24**: present in routing table
- ✅ **leaf2 route 0.0.0.0/0**: present in routing table
- ✅ **edge1 container exists**: clab-mini-fabric-lab-edge1 is running
- ✅ **edge1 BGP peer 172.16.0.0**: expected Established, got Established
- ✅ **edge1 BGP peer 172.16.0.2**: expected Established, got Established
- ✅ **edge1 route 192.168.1.0/24**: present in routing table
- ✅ **edge1 route 192.168.2.0/24**: present in routing table
- ✅ **h1 ping 192.168.2.10**: reachable
- ✅ **h2 ping 192.168.1.10**: reachable
