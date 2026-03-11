import socket

MAX_SIZE_BYTES = 65535  # Mazimum size of a UDP datagram
port = 3000
host = "127.0.0.1"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

hosts = set()
while True:
    hosts.add((host, port))
    message = input("Input message to send to server:")
    data = message.encode("ascii")
    s.sendto(data, (host, port))
    data, address = s.recvfrom(MAX_SIZE_BYTES)
    text = data.decode("ascii")
    if address in hosts:
        print("The server {} replied with {!r}".format(address, text))
        hosts.remove(address)
    else:
        print("message {!r} from unexpected host {}!".format(text, address))
