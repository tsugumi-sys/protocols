"""Small executable demo for the RIP simulation."""

from topology_reader import topology_to_routers


def main() -> None:
    topology = [
        ("10.0.0.1", ("192.168.1.1", "10.0.0.2", "192.168.1.2", 1)),
        (
            "10.0.0.2",
            ("192.168.1.2", "10.0.0.1", "192.168.1.1", 1),
            ("192.168.2.1", "10.0.0.3", "192.168.2.2", 1),
        ),
        ("10.0.0.3", ("192.168.2.2", "10.0.0.2", "192.168.2.1", 1)),
    ]

    routers = topology_to_routers(topology)
    for router in routers:
        router.send_rip_packets(routers)

    for router in routers:
        print()
        router.print_router()


if __name__ == "__main__":
    main()
