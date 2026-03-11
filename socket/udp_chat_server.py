import socket

MAX_SIZE_BYTES = 65535

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

port = 3000
hostname = "127.0.0.1"
s.bind((hostname, port))

while True:
    data, clientAddress = s.recvfrom(MAX_SIZE_BYTES)
    message = data.decode("ascii")
    print("The client at {} says {!r}".format(clientAddress, message))
    reply_msg = "Hello from server"
    data = reply_msg.encode("ascii")
    s.sendto(data, clientAddress)
