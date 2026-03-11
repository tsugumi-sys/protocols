import socket

MAX_SIZE_BYTES = 65535  # Mazimum size of a UDP datagram

s = socket.socket(
    socket.AF_INET, socket.SOCK_DGRAM
)  # AF_INET: use IPv4 address. SOCK_DGGRAM: use UDP
print(
    s
)  # <socket.socket fd=3, family=2, type=2, proto=0, laddr=('0.0.0.0', 0)> '0.0.0.0' means, this socket recieves all the packets from the outside.

port = 3000
hostname = "127.0.0.1"  # only accessbile within the localhost netwotk.
s.bind((hostname, port))

print(s)  # <socket.socket fd=3, family=2, type=2, proto=0, laddr=('127.0.0.1', 3000)>
print(
    "Listening at {}".format(s.getsockname())
)  # Printing the IP address and port of socket

while True:
    # The code to handle clients will go here
    data, clientAddress = s.recvfrom(
        MAX_SIZE_BYTES
    )  # Receive at most 65535 bytes at once
    message = data.decode("ascii")
    upperCaseMessage = message.upper()
    print("The client at {} says {!r}".format(clientAddress, message))
    data = upperCaseMessage.encode("ascii")
    s.sendto(data, clientAddress)
