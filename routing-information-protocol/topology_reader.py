"""Helpers for building routers from a compact topology definition.

The accepted topology format is:
    [
        (
            "<router-ip>",
            ("<local-port-ip>", "<neighbor-router-ip>", "<neighbor-port-ip>", <cost>),
            ...
        ),
        ...
    ]

Example:
    >>> routers = topology_to_routers([
    ...     ("10.0.0.1", ("192.168.1.1", "10.0.0.2", "192.168.1.2", 1)),
    ...     ("10.0.0.2", ("192.168.1.2", "10.0.0.1", "192.168.1.1", 1)),
    ... ])
    >>> [router.ip_address for router in routers]
    ['10.0.0.1', '10.0.0.2']
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from port import Port, PortLink
from router import Router


TopologyPort = tuple[str, str, str, int]
TopologyRouter = tuple[str, *tuple[TopologyPort, ...]]


def topology_to_routers(topology: Iterable[Sequence[object]]) -> list[Router]:
    """Convert a topology description into initialized router objects."""
    router_list: list[Router] = []

    for raw_router in topology:
        router_ip = str(raw_router[0])
        router_instance = Router(router_ip, [], [])

        for raw_port in raw_router[1:]:
            port_ip, dest_ip_address, dest_port_ip, cost = raw_port
            link = PortLink(str(dest_ip_address), str(dest_port_ip), int(cost))
            router_instance.add_port(Port(str(port_ip), link))

        router_instance.add_rip_entry(None, router_ip, 0, None)
        router_list.append(router_instance)

    return router_list
