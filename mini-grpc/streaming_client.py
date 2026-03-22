import base64
import socket
import uuid

from framings import recv_message, send_message


# ────────────────────────────
# Client config ⚙️
# ────────────────────────────

HOST = "127.0.0.1"
PORT = 50051


# ────────────────────────────
# Helpers 🧰
# ────────────────────────────


def encode_text_chunk(text: str) -> str:
    """Encode a UTF-8 string as base64 for transport."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def main() -> None:
    stream_id = str(uuid.uuid4())

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"[client] connected to {HOST}:{PORT}")

        # 1. Start stream
        start_message = {
            "version": 1,
            "type": "stream_start",
            "stream_id": stream_id,
            "method": "UploadService/ConcatText",
            "meta": {
                "content_type": "text/plain",
                "encoding": "utf-8",
            },
        }
        send_message(client, start_message)
        print("[client] sent stream_start")

        # 2. Wait for ack
        ack = recv_message(client)
        print("[client] received:", ack)

        if ack.get("type") != "stream_start_ack" or not ack.get("ok"):
            raise RuntimeError(f"stream start rejected: {ack}")

        # 3. Send chunks
        chunks = ["Hello, ", "mini ", "gRPC ", "streaming!"]

        for seq, chunk_text in enumerate(chunks, start=1):
            chunk_message = {
                "version": 1,
                "type": "stream_chunk",
                "stream_id": stream_id,
                "seq": seq,
                "payload": encode_text_chunk(chunk_text),
            }
            send_message(client, chunk_message)
            print(f"[client] sent chunk seq={seq}: {chunk_text!r}")

        # 4. Send end
        end_message = {
            "version": 1,
            "type": "stream_end",
            "stream_id": stream_id,
        }
        send_message(client, end_message)
        print("[client] sent stream_end")

        # 5. Receive final result
        result = recv_message(client)
        print("[client] received:", result)


if __name__ == "__main__":
    main()
