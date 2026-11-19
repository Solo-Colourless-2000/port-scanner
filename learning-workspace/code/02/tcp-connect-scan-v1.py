import sys
from scapy.all import IP, TCP, sr1, conf, L3RawSocket

dst_ip = sys.argv[1]
port = int(sys.argv[2])

conf.L3socket = L3RawSocket

ip_packet = IP(dst=dst_ip)
tcp_syn = TCP(dport=port, flags="S")
ip_tcp_syn = ip_packet / tcp_syn

print("Sending a SYN packet...")
response = sr1(ip_tcp_syn, timeout=2)

print(f"-----\nResponse: {response}\n-----")

# If the client receives a SYN/ACK packet from the server, it sends an ACK packet to the server.
if response is not None and response.haslayer(TCP) and response[TCP].flags == "SA":
    tcp_ack = TCP(
            dport=port,
            sport=tcp_syn.sport,
            seq=response[TCP].ack, 
            ack=response[TCP].seq + 1, 
            flags="A"
    ) 
    ip_tcp_ack = ip_packet / tcp_ack
    ack_reply = sr1(ip_tcp_ack, timeout=3)

    print(f"-----\nResult: {ack_reply}\n-----")
elif response is not None and response.haslayer(TCP) and response[TCP].flags != "SA":
    print(f"-----\nResult: Response is not SYN/ACK\n-----")
elif response is None:
    print(f"-----\nResult: No Response\n-----")
else:
    print(f"-----\nResult: Unexpected non-TCP response\n-----")

