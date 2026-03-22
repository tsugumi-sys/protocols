import json
import socket
import struct
from typing import Any


# ────────────────────────────
# Protocol constants 📦
# ────────────────────────────

MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MiB per message


# ────────────────────────────
# Framing helpers 🌐
# ────────────────────────────


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """Receive exactly `size` bytes from the socket."""
    chunks: list[bytes] = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("socket closed while receiving data")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def send_message(sock: socket.socket, message: dict[str, Any]) -> None:
    """Serialize a message as JSON and send it with a 4-byte length prefix."""
    body = json.dumps(message).encode("utf-8")
    if len(body) > MAX_MESSAGE_SIZE:
        raise ValueError(f"message too large: {len(body)} bytes")

    header = struct.pack("!I", len(body))
    sock.sendall(header + body)


def recv_message(sock: socket.socket) -> dict[str, Any]:
    """Receive one length-prefixed JSON message."""
    header = recv_exact(sock, 4)
    (length,) = struct.unpack("!I", header)

    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"message too large: {length} bytes")

    body = recv_exact(sock, length)
    message = json.loads(body.decode("utf-8"))

    if not isinstance(message, dict):
        raise ValueError("message must be a JSON object")

    return message
