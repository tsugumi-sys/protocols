"""RIP packet and routing entry models.

Example:
    >>> entry = RipEntry(port_ip="192.168.1.1", cost=1, dest_ip_address="10.0.0.2", next_hop_ip="10.0.0.2")
    >>> packet = RipPacket([entry])
    >>> packet.rip_entry_count
    1
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RipEntry:
    """A single route in a router's RIP table."""

    port_ip: str | None
    cost: int
    dest_ip_address: str
    next_hop_ip: str | None

    def get_port_ip(self) -> str | None:
        return self.port_ip

    def set_port_ip(self, port_ip: str | None) -> None:
        self.port_ip = port_ip

    def get_cost(self) -> int:
        return self.cost

    def set_cost(self, cost: int) -> None:
        self.cost = cost

    def get_dest_address(self) -> str:
        return self.dest_ip_address

    def set_dest_address(self, dest_ip_address: str) -> None:
        self.dest_ip_address = dest_ip_address

    def get_next_hop(self) -> str | None:
        return self.next_hop_ip

    def set_next_hop(self, next_hop: str | None) -> None:
        self.next_hop_ip = next_hop

    def print_rip_entry(self) -> None:
        print(self.return_rip_entry())

    def return_rip_entry(self) -> str:
        return (
            f"{self.port_ip} | {self.dest_ip_address} | "
            f"{self.next_hop_ip} | {self.cost}"
        )


@dataclass(slots=True)
class RipPacket:
    """A RIP packet containing one or more route advertisements."""

    rip_entries: list[RipEntry] = field(default_factory=list)

    def add_rip_entry(self, rip_entry: RipEntry) -> None:
        self.rip_entries.append(rip_entry)

    def add_rip_entries(self, rip_entries: list[RipEntry]) -> None:
        self.rip_entries.extend(rip_entries)

    @property
    def rip_entry_count(self) -> int:
        return len(self.rip_entries)

    def print_rip_packet(self) -> None:
        for index, entry in enumerate(self.rip_entries, start=1):
            print(f"RIP entry #: {index}")
            entry.print_rip_entry()

    def return_rip_packet(self) -> list[str]:
        return [entry.return_rip_entry() for entry in self.rip_entries]


# Backward-compatible aliases for older imports.
RIP_entry = RipEntry
RIP_packet = RipPacket
