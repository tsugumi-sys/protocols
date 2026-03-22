import base64
import socket
from enum import Enum
from typing import Any

from framings import recv_message, send_message


# ────────────────────────────
# Server config ⚙️
# ────────────────────────────

HOST = "127.0.0.1"
PORT = 50051
SUPPORTED_METHODS = {"UploadService/ConcatText"}


# ────────────────────────────
# State machine 🎛️
# ────────────────────────────


class StreamState(str, Enum):
    WAIT_START = "WAIT_START"
    WAIT_CHUNKS = "WAIT_CHUNKS"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"


# ────────────────────────────
# Business logic 🧠
# ────────────────────────────


def process_stream(
    method: str, meta: dict[str, Any], chunks: list[str]
) -> dict[str, Any]:
    """
    Process the received stream.

    Current demo method:
    - UploadService/ConcatText:
      base64-encoded UTF-8 text chunks are concatenated and returned.
    """
    if method != "UploadService/ConcatText":
        raise ValueError(f"unsupported method: {method}")

    decoded_parts: list[str] = []
    for chunk in chunks:
        raw = base64.b64decode(chunk)
        decoded_parts.append(raw.decode("utf-8"))

    text = "".join(decoded_parts)

    return {
        "text": text,
        "chunk_count": len(chunks),
        "meta": meta,
    }


# ────────────────────────────
# Session handler 🔌
# ────────────────────────────


class ConnectionSession:
    def __init__(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        self.conn = conn
        self.addr = addr
        self.state = StreamState.WAIT_START
        self.stream_id: str | None = None
        self.method: str | None = None
        self.meta: dict[str, Any] = {}
        self.chunks: list[str] = []
        self.expected_seq = 1

    def run(self) -> None:
        """Run the session until finished or an error occurs."""
        print(f"[session] connected: {self.addr}")

        try:
            while self.state != StreamState.FINISHED:
                message = recv_message(self.conn)
                self.handle_message(message)
        except ConnectionError:
            print(f"[session] client disconnected: {self.addr}")
        except Exception as exc:
            self.send_error(
                stream_id=self.stream_id,
                code="INTERNAL_ERROR",
                message=str(exc),
            )
        finally:
            self.conn.close()
            print(f"[session] closed: {self.addr}")

    def handle_message(self, message: dict[str, Any]) -> None:
        """Dispatch a message according to the current state."""
        if self.state == StreamState.WAIT_START:
            self.handle_wait_start(message)
        elif self.state == StreamState.WAIT_CHUNKS:
            self.handle_wait_chunks(message)
        else:
            raise ValueError(f"invalid state: {self.state}")

    def handle_wait_start(self, message: dict[str, Any]) -> None:
        """Handle the first stream_start message."""
        if message.get("type") != "stream_start":
            self.send_error(
                stream_id=None,
                code="INVALID_STATE",
                message="expected stream_start",
            )
            self.state = StreamState.FINISHED
            return

        stream_id = message.get("stream_id")
        method = message.get("method")
        meta = message.get("meta", {})

        if not isinstance(stream_id, str) or not stream_id:
            self.send_start_ack(
                stream_id=None,
                ok=False,
                error={
                    "code": "INVALID_STREAM_ID",
                    "message": "stream_id must be a non-empty string",
                },
            )
            self.state = StreamState.FINISHED
            return

        if not isinstance(method, str) or method not in SUPPORTED_METHODS:
            self.send_start_ack(
                stream_id=stream_id,
                ok=False,
                error={
                    "code": "UNSUPPORTED_METHOD",
                    "message": f"unsupported method: {method}",
                },
            )
            self.state = StreamState.FINISHED
            return

        if not isinstance(meta, dict):
            self.send_start_ack(
                stream_id=stream_id,
                ok=False,
                error={
                    "code": "INVALID_META",
                    "message": "meta must be an object",
                },
            )
            self.state = StreamState.FINISHED
            return

        self.stream_id = stream_id
        self.method = method
        self.meta = meta

        self.send_start_ack(stream_id=stream_id, ok=True, error=None)
        self.state = StreamState.WAIT_CHUNKS

    def handle_wait_chunks(self, message: dict[str, Any]) -> None:
        """Handle stream_chunk and stream_end messages."""
        msg_type = message.get("type")
        stream_id = message.get("stream_id")

        if stream_id != self.stream_id:
            self.send_error(
                stream_id=self.stream_id,
                code="INVALID_STREAM_ID",
                message=f"expected stream_id={self.stream_id}, got {stream_id}",
            )
            self.state = StreamState.FINISHED
            return

        if msg_type == "stream_chunk":
            self.handle_stream_chunk(message)
            return

        if msg_type == "stream_end":
            self.handle_stream_end()
            return

        self.send_error(
            stream_id=self.stream_id,
            code="INVALID_STATE",
            message="expected stream_chunk or stream_end",
        )
        self.state = StreamState.FINISHED

    def handle_stream_chunk(self, message: dict[str, Any]) -> None:
        """Validate and store one chunk."""
        seq = message.get("seq")
        payload = message.get("payload")

        if not isinstance(seq, int) or seq < 1:
            self.send_error(
                stream_id=self.stream_id,
                code="INVALID_SEQUENCE",
                message="seq must be a positive integer",
            )
            self.state = StreamState.FINISHED
            return

        if seq != self.expected_seq:
            self.send_error(
                stream_id=self.stream_id,
                code="INVALID_SEQUENCE",
                message=f"expected seq={self.expected_seq}, got seq={seq}",
            )
            self.state = StreamState.FINISHED
            return

        if not isinstance(payload, str):
            self.send_error(
                stream_id=self.stream_id,
                code="INVALID_PAYLOAD",
                message="payload must be a base64 string",
            )
            self.state = StreamState.FINISHED
            return

        # Validate that payload is actually base64.
        try:
            base64.b64decode(payload, validate=True)
        except Exception:
            self.send_error(
                stream_id=self.stream_id,
                code="INVALID_PAYLOAD",
                message="payload is not valid base64",
            )
            self.state = StreamState.FINISHED
            return

        self.chunks.append(payload)
        self.expected_seq += 1

    def handle_stream_end(self) -> None:
        """Process the full stream and return the final result."""
        self.state = StreamState.PROCESSING

        try:
            result = process_stream(
                method=self.method or "",
                meta=self.meta,
                chunks=self.chunks,
            )
            self.send_result(
                stream_id=self.stream_id,
                ok=True,
                result=result,
                error=None,
            )
        except Exception as exc:
            self.send_result(
                stream_id=self.stream_id,
                ok=False,
                result=None,
                error={
                    "code": "PROCESSING_ERROR",
                    "message": str(exc),
                },
            )
        finally:
            self.state = StreamState.FINISHED

    def send_start_ack(
        self,
        stream_id: str | None,
        ok: bool,
        error: dict[str, Any] | None,
    ) -> None:
        send_message(
            self.conn,
            {
                "version": 1,
                "type": "stream_start_ack",
                "stream_id": stream_id,
                "ok": ok,
                "error": error,
            },
        )

    def send_error(self, stream_id: str | None, code: str, message: str) -> None:
        try:
            send_message(
                self.conn,
                {
                    "version": 1,
                    "type": "stream_error",
                    "stream_id": stream_id,
                    "error": {
                        "code": code,
                        "message": message,
                    },
                },
            )
        except Exception:
            pass

    def send_result(
        self,
        stream_id: str | None,
        ok: bool,
        result: dict[str, Any] | None,
        error: dict[str, Any] | None,
    ) -> None:
        send_message(
            self.conn,
            {
                "version": 1,
                "type": "stream_result",
                "stream_id": stream_id,
                "ok": ok,
                "result": result,
                "error": error,
            },
        )


# ────────────────────────────
# TCP server 🚀
# ────────────────────────────


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"[server] listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            session = ConnectionSession(conn=conn, addr=addr)
            session.run()


if __name__ == "__main__":
    main()
