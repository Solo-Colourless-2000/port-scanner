import sys
from scapy.all import IP, TCP, sr1, conf, L3RawSocket

dst_ip = sys.argv[1]
port = int(sys.argv[2])

conf.L3socket = L3RawSocket

ip_packet = IP(dst=dst_ip)
tcp = TCP(dport=port, flags="S")
ip_tcp = ip_packet / tcp

print("Sending a SYN packet...")
response = sr1(ip_tcp, timeout=2)

print(f"-----\nResponse: {response}\n-----")

# If the client captures a response with a SYN/ACK packet from a server, it respond to the server with an ACK packet.
if response is not None and response.haslayer(TCP) and response[TCP].flags == "SA":

    ack = TCP(dport=port, response[TCP].seq, response[TCP].ack, flags="A") 
    ack_reply = sr1(ack, timeout=3)

    print(f"-----\nResult: {ack_reply}\n-----")
else if :
    print(f"-----\nResult: Response is not SYN/ACK\n-----")
    
else:

    print(f"-----\nResult: No Response or response timeout\n-----")



