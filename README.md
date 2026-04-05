# mini-fabric-lab
A reproducible container-based network lab that models a small fabric: OSPF underlay for reachability, iBGP overlay with route reflectors for scalable route distribution, and an eBGP edge that injects a default route and receives internal prefixes. I automated verification with a Python health-check that parses FRR JSON show outputs
