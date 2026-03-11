import socket


def recvall(sock, length):
    """
    if length = 16, and actual sent data is 16 bytes, however tcp receives like

    recv → "Goodby"
    recv → "e, cl"
    recv → "ient!"

    In that case, we need to read all data.
    """
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError(
                "was expecting %d bytes but only received"
                " %d bytes before the socket closed" % (length, len(data))
            )
        data += more
    return data


def client(port):
    host = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("Client has been assigned the socket: ", sock.getsockname())
    sock.sendall(b"Greetings, server")
    reply = recvall(sock, 16)  # server sents 16 bytes data, so we read 16 bytes data.
    print("Server: ", repr(reply))
    sock.close()


client(3000)
