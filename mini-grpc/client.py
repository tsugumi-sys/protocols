import socket
import uuid
from framings import recv_message, send_message

HOST = "127.0.0.1"
PORT = 50051

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))

    req1 = {
        "version": 1,
        "request_id": str(uuid.uuid4()),
        "method": "ping",
        "params": {},
    }
    send_message(client, req1)
    print(recv_message(client))

    req2 = {
        "version": 1,
        "request_id": str(uuid.uuid4()),
        "method": "add",
        "params": {"a": 10, "b": 20},
    }
    send_message(client, req2)
    print(recv_message(client))

    req3 = {
        "version": 1,
        "request_id": str(uuid.uuid4()),
        "method": "echo",
        "params": {"message": "hello"},
    }
    send_message(client, req3)
    print(recv_message(client))
