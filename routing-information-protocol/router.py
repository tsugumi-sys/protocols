"""Router models and RIP update logic.

Example:
    >>> from topology_reader import topology_to_routers
    >>> routers = topology_to_routers([
    ...     ("10.0.0.1", ("192.168.1.1", "10.0.0.2", "192.168.1.2", 1)),
    ...     ("10.0.0.2", ("192.168.1.2", "10.0.0.1", "192.168.1.1", 1)),
    ... ])
    >>> router_a, router_b = routers
    >>> router_a.send_rip_packets(routers)
    [Router(ip_address='10.0.0.1'), Router(ip_address='10.0.0.2')]
    >>> router_b.find_rip_entry("10.0.0.1").cost
    1
"""

from __future__ import annotations

from rip_packet import RipEntry, RipPacket
from port import Port, PortLink


class RouterBase:
    """Shared router state and utility methods."""

    def __init__(
        self, ip_address: str, rip_entries: list[RipEntry] | None = None, ports: list[Port] | None = None
    ) -> None:
        self.ip_address = ip_address
        self.rip_entries = rip_entries or []
        self.ports = ports or []

    def __repr__(self) -> str:
        return f"Router(ip_address={self.ip_address!r})"

    @property
    def IP_address(self) -> str:
        return self.ip_address

    @IP_address.setter
    def IP_address(self, value: str) -> None:
        self.ip_address = value

    def add_port(self, router_port: Port) -> None:
        self.ports.append(router_port)

    def add_rip_entry(
        self, port_ip: str | None, dest_ip: str, cost: int, next_hop_ip: str | None
    ) -> RipEntry:
        new_rip_entry = RipEntry(port_ip, cost, dest_ip, next_hop_ip)
        self.rip_entries.append(new_rip_entry)
        return new_rip_entry

    def add_RIP_entry(
        self, port_IP: str | None, dest_IP: str, cost: int, next_hop_IP: str | None
    ) -> RipEntry:
        return self.add_rip_entry(port_IP, dest_IP, cost, next_hop_IP)

    def find_rip_entry(self, destination_ip_to_find: str) -> RipEntry | None:
        for entry in self.rip_entries:
            if entry.dest_ip_address == destination_ip_to_find:
                return entry
        return None

    def find_RIP_entry(self, destination_IP_to_find: str) -> RipEntry | None:
        return self.find_rip_entry(destination_IP_to_find)

    def set_rip_entry_cost(self, destination_ip_to_find: str, new_cost: int) -> None:
        entry = self.find_rip_entry(destination_ip_to_find)
        if entry is not None:
            entry.set_cost(new_cost)

    def set_RIP_entry_cost(self, destination_IP_to_find: str, new_cost: int) -> None:
        self.set_rip_entry_cost(destination_IP_to_find, new_cost)

    def delete_rip_entry(self, destination_ip_to_find: str) -> None:
        entry = self.find_rip_entry(destination_ip_to_find)
        if entry is not None:
            self.rip_entries.remove(entry)

    def delete_RIP_entry(self, destination_IP_to_find: str) -> None:
        self.delete_rip_entry(destination_IP_to_find)

    def print_router(self) -> None:
        for line in self.return_router():
            print(line)

    def return_router(self) -> list[str]:
        lines = [
            f"~~~~ Router IP address = {self.ip_address} ~~~~",
            "---Ports---",
            "Port IP | Destination Router IP | Destination Port IP | Cost",
        ]
        lines.extend(router_port.return_port() for router_port in self.ports)
        lines.append("---RIP entries---")
        lines.append("port IP | destination IP address | next hop | cost")
        lines.extend(entry.return_rip_entry() for entry in self.rip_entries)
        return lines

    def build_rip_packet(self) -> RipPacket:
        """Return a snapshot of the current routing table for advertisement."""
        packet_entries = [
            RipEntry(entry.port_ip, entry.cost, entry.dest_ip_address, entry.next_hop_ip)
            for entry in self.rip_entries
        ]
        return RipPacket(packet_entries)

    def find_port_to_neighbor(self, neighbor_ip: str) -> Port | None:
        for router_port in self.ports:
            if router_port.link is not None and router_port.link.dest_ip_address == neighbor_ip:
                return router_port
        return None

    def find_router(self, routers: list["RouterBase"], ip_address: str) -> "RouterBase" | None:
        for other_router in routers:
            if other_router.ip_address == ip_address:
                return other_router
        return None


class Router(RouterBase):
    """A simple RIP router that exchanges full routing tables with neighbors."""

    def send_rip_packets(self, routers: list[RouterBase]) -> list[RouterBase]:
        """Advertise the current routing table to directly connected neighbors."""
        for router_port in self.ports:
            if router_port.link is None:
                continue

            neighbor_ip = router_port.link.dest_ip_address
            neighbor = self.find_router(routers, neighbor_ip)
            if neighbor is None:
                continue

            neighbor.receive_rip_packets(
                self.build_rip_packet(),
                router_port.link,
                routers,
                self.ip_address,
            )
        return routers

    def send_RIP_packets(self, routers: list[RouterBase]) -> list[RouterBase]:
        return self.send_rip_packets(routers)

    def receive_rip_packets(
        self,
        rip_packet: RipPacket,
        link_send_on: PortLink,
        routers: list[RouterBase],
        next_hop_ip: str,
    ) -> list[RouterBase]:
        """Update the routing table from a received RIP advertisement.

        The new route cost is the neighbor link cost plus the cost advertised
        by the sender. If the route is unknown, or if the same next hop has a
        changed metric, or if a cheaper route is discovered, the route entry is
        updated.
        """

        recv_port = self.find_port_to_neighbor(next_hop_ip)
        recv_port_ip = recv_port.port_ip if recv_port is not None else None

        for entry in rip_packet.rip_entries:
            if entry.dest_ip_address == self.ip_address:
                continue

            new_cost = link_send_on.cost + entry.cost
            existing_entry = self.find_rip_entry(entry.dest_ip_address)

            if existing_entry is None:
                self.add_rip_entry(
                    recv_port_ip, entry.dest_ip_address, new_cost, next_hop_ip
                )
                continue

            if existing_entry.next_hop_ip == next_hop_ip or new_cost < existing_entry.cost:
                existing_entry.set_cost(new_cost)
                existing_entry.set_next_hop(next_hop_ip)
                existing_entry.set_port_ip(recv_port_ip)

        return routers

    def receive_RIP_packets(
        self,
        rip_packet: RipPacket,
        link_send_on: PortLink,
        routers: list[RouterBase],
        next_hop_IP: str,
    ) -> list[RouterBase]:
        return self.receive_rip_packets(rip_packet, link_send_on, routers, next_hop_IP)


# Backward-compatible aliases for older imports.
router_base = RouterBase
router = Router
