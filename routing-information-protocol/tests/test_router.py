from topology_reader import topology_to_routers


def build_linear_topology():
    return [
        ("10.0.0.1", ("192.168.1.1", "10.0.0.2", "192.168.1.2", 1)),
        (
            "10.0.0.2",
            ("192.168.1.2", "10.0.0.1", "192.168.1.1", 1),
            ("192.168.2.1", "10.0.0.3", "192.168.2.2", 1),
        ),
        ("10.0.0.3", ("192.168.2.2", "10.0.0.2", "192.168.2.1", 1)),
    ]


def get_router(routers, ip_address):
    return next(router for router in routers if router.ip_address == ip_address)


def test_topology_initializes_self_routes():
    routers = topology_to_routers(build_linear_topology())

    router_a = get_router(routers, "10.0.0.1")
    entry = router_a.find_rip_entry("10.0.0.1")

    assert entry is not None
    assert entry.cost == 0
    assert entry.next_hop_ip is None


def test_send_rip_packets_shares_direct_neighbor_route():
    routers = topology_to_routers(build_linear_topology())

    router_a = get_router(routers, "10.0.0.1")
    router_b = get_router(routers, "10.0.0.2")
    router_a.send_rip_packets(routers)

    entry = router_b.find_rip_entry("10.0.0.1")

    assert entry is not None
    assert entry.cost == 1
    assert entry.next_hop_ip == "10.0.0.1"
    assert entry.port_ip == "192.168.1.2"


def test_router_learns_two_hop_route_after_multiple_advertisements():
    routers = topology_to_routers(build_linear_topology())

    router_a = get_router(routers, "10.0.0.1")
    router_b = get_router(routers, "10.0.0.2")
    router_c = get_router(routers, "10.0.0.3")

    router_a.send_rip_packets(routers)
    router_b.send_rip_packets(routers)

    entry = router_c.find_rip_entry("10.0.0.1")

    assert entry is not None
    assert entry.cost == 2
    assert entry.next_hop_ip == "10.0.0.2"
    assert entry.port_ip == "192.168.2.2"


def test_receive_rip_packets_updates_route_when_same_next_hop_cost_changes():
    routers = topology_to_routers(build_linear_topology())

    router_a = get_router(routers, "10.0.0.1")
    router_b = get_router(routers, "10.0.0.2")

    router_a.send_rip_packets(routers)
    initial_entry = router_b.find_rip_entry("10.0.0.1")
    assert initial_entry is not None
    assert initial_entry.cost == 1

    initial_entry.set_cost(5)
    router_a.send_rip_packets(routers)

    updated_entry = router_b.find_rip_entry("10.0.0.1")

    assert updated_entry is not None
    assert updated_entry.cost == 1
