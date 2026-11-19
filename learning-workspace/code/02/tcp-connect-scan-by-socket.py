import socket
import sys

ip_address = sys.argv[1]
port = int(sys.argv[2])

connection = socket.socket()
tcp_connect = connection.connect_ex((ip_address, port))

connection.close()

if tcp_connect == 0:
    print(f"TCP port {port} is open.")
else:
    print(f"TCP port {port} is closed.")

