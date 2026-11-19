from scapy.all import sniff


def print_packet(packet):
	packet.show()
	
sniffed_p = sniff(filter="icmp and src host 127.0.0.1 and dst host 127.0.0.1", prn=print_packet, count=5, iface="lo")
