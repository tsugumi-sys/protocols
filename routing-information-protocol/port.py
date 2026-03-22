"""Port and link models used by the RIP simulation.

Example:
    >>> link = PortLink("10.0.0.2", "192.168.1.2", 1)
    >>> port = Port("192.168.1.1", link)
    >>> port.return_port()
    '192.168.1.1 | 10.0.0.2 | 192.168.1.2 | 1'
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PortLink:
    """Represents a point-to-point link from one port to a neighbor."""

    dest_ip_address: str
    dest_port_ip: str
    cost: int

    def set_dest_ip_address(self, ip_address: str) -> None:
        self.dest_ip_address = ip_address

    def set_dest_port_ip(self, port_ip: str) -> None:
        self.dest_port_ip = port_ip

    def print_link(self) -> None:
        print(self.return_link())

    def return_link(self) -> str:
        return (
            f"destination router IP = {self.dest_ip_address}\n"
            f"destination router port IP = {self.dest_port_ip}\n"
            f"cost = {self.cost}"
        )


@dataclass(slots=True)
class Port:
    """Represents a router interface and its optional link."""

    port_ip: str
    link: PortLink | None = None

    def set_link(self, dest_router_ip_address: str, dest_port: str, cost: int) -> None:
        """Create or update the link attached to this port."""
        if self.link is None:
            self.link = PortLink(dest_router_ip_address, dest_port, cost)
            return

        self.link.set_dest_port_ip(dest_port)
        self.link.set_dest_ip_address(dest_router_ip_address)
        self.link.cost = cost

    def get_link(self) -> PortLink | None:
        return self.link

    def delete_link(self) -> None:
        self.link = None

    def print_port(self) -> None:
        print(self.return_port())

    def return_port(self) -> str:
        if self.link is None:
            return f"{self.port_ip} | None | None | None"

        return (
            f"{self.port_ip} | {self.link.dest_ip_address} | "
            f"{self.link.dest_port_ip} | {self.link.cost}"
        )


# Backward-compatible aliases for older imports.
port_link = PortLink
port = Port
