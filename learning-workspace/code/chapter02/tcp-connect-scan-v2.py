import sys
from scapy.all import IP, TCP, sr1, conf, L3RawSocket

target_ip = sys.argv[1]
target_port = int(sys.argv[2])

conf.L3socket = L3RawSocket

ip_layer = IP(dst=target_ip)
syn_tcp_layer = TCP(dport=target_port, flags="S")
syn_packet = ip_layer / syn_tcp_layer

print("Sending a SYN packet...")
syn_response = sr1(syn_packet, timeout=3)

print(f"-----\nResponse: {syn_response}\n-----")

# If the client receives a SYN/ACK packet from the server, it sends an ACK packet to the server.
if syn_response is not None and syn_response.haslayer(TCP) and syn_response[TCP].flags == "SA":
    ack_tcp_layer = TCP(
            dport=target_port,
            sport=syn_tcp_layer.sport,
            seq=syn_response[TCP].ack, 
            ack=syn_response[TCP].seq + 1, 
            flags="A"
    ) 
    ack_packet = ip_layer / ack_tcp_layer

    ack_response = sr1(ack_packet, timeout=3)
    print(f"-----\nACK response: {ack_response}\n-----")

    # Build a FIN/ACK packet for a proper TCP shutdown.
    fin_ack_tcp_layer = TCP(
            dport=target_port,
            sport=syn_tcp_layer.sport,
            seq=syn_response[TCP].ack,
            ack=syn_response[TCP].seq + 1,
            flags="FA"
    )
    fin_ack_packet = ip_layer / fin_ack_tcp_layer

    print("Sending a FIN/ACK packet...")
    fin_response = sr1(fin_ack_packet, timeout=3)
    print(f"-----\nFIN/ACK response: {fin_response}\n-----")

    if fin_response is not None and fin_response.haslayer(TCP) and fin_response[TCP].flags == "FA":
        final_ack_tcp_layer = TCP(dport=target_port,
            sport=syn_tcp_layer.sport,
            seq=fin_response[TCP].ack,
            ack=fin_response[TCP].seq + 1,
            flags="A"
        )
        final_ack_packet = ip_layer / final_ack_tcp_layer

        final_ack_response = sr1(final_ack_packet, timeout=3)
    elif fin_response is not None and fin_response.haslayer(TCP) and fin_response[TCP].flags != "FA":
        print(f"-----\nResult: Response is not FIN/ACK\n-----")
    elif fin_response is None:
        print(f"-----\nResult: No Response\n-----")
    else:
        print(f"-----\nResult: Unexpected non-TCP response\n-----")

elif syn_response is not None and syn_response.haslayer(TCP) and syn_response[TCP].flags != "SA":
    print(f"-----\nResult: Response is not SYN/ACK\n-----")
elif syn_response is None:
    print(f"-----\nResult: No Response\n-----")
else:
    print(f"-----\nResult: Unexpected non-TCP response\n-----")

"""
| 変数名                 | 内容                 |
| --------------------- | ------------------ |
| `target_ip`           | スキャン対象のIPアドレス |
| `target_port`         | 宛先ポート         |
| `ip_layer`            | この時点ではIP層だけを構築 |
| `syn_tcp_layer`       | SYN用のTCPヘッダー       |
| `syn_packet`          | 実際に送信するSYNパケット     |
| `syn_response`        | SYNに対する応答          |
| `ack_tcp_layer`       | ACK用のTCPヘッダー       |
| `ack_packet`          | 送信するACKパケット        |
| `ack_response`        | ACK送信後に受信した応答      |
| `fin_ack_tcp_layer`   | FIN/ACK用のTCPヘッダー   |
| `fin_ack_packet`      | 送信するFIN/ACKパケット    |
| `fin_response`        | FIN/ACK送信後の応答      |
| `final_ack_tcp_layer` | 最後のACK用TCPヘッダー     |
| `final_ack_packet`    | 最後に送信するACKパケット     |
| `final_ack_response`  | 最後のACK送信後の応答       |
"""