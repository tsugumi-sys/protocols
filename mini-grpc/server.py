import socket
from typing import Any

from framings import recv_message, send_message

# ────────────────────────────
# RPC method handlers 🛠️
# ────────────────────────────


def handle_echo(params: dict[str, Any]) -> dict[str, Any]:
    return {"message": params["message"]}


def handle_add(params: dict[str, Any]) -> int:
    return params["a"] + params["b"]


def handle_ping(params: dict[str, Any]) -> str:
    return "pong"


METHODS = {
    "echo": handle_echo,
    "add": handle_add,
    "ping": handle_ping,
}


# ────────────────────────────
# Request dispatcher 🚦
# ────────────────────────────


def dispatch(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("request_id")
    version = request.get("version", 1)
    method = request.get("method")
    params = request.get("params", {})

    if method not in METHODS:
        return {
            "version": version,
            "request_id": request_id,
            "ok": False,
            "result": None,
            "error": {
                "code": "METHOD_NOT_FOUND",
                "message": f"unknown method: {method}",
            },
        }

    try:
        result = METHODS[method](params)
        return {
            "version": version,
            "request_id": request_id,
            "ok": True,
            "result": result,
            "error": None,
        }
    except KeyError as e:
        return {
            "version": version,
            "request_id": request_id,
            "ok": False,
            "result": None,
            "error": {
                "code": "INVALID_PARAMS",
                "message": f"missing parameter: {e}",
            },
        }
    except Exception as e:
        return {
            "version": version,
            "request_id": request_id,
            "ok": False,
            "result": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        }


# ────────────────────────────
# TCP server 🌐
# ────────────────────────────

HOST = "127.0.0.1"
PORT = 50051

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"RPC server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print("connected:", addr)

        with conn:
            try:
                while True:
                    request = recv_message(conn)
                    print("request:", request)

                    response = dispatch(request)
                    send_message(conn, response)

            except ConnectionError:
                print("client disconnected:", addr)
            except Exception as e:
                print("unexpected server error:", e)
