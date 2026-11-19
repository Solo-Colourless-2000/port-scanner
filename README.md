# Port Scanner

A personal project for learning port scanning, networking, and penetration testing.

This project is based on the book and its official sample code listed below, rather than being developed entirely from scratch.

## References

- **Book:** [ポートスキャナ自作ではじめるペネトレーションテスト](https://www.oreilly.co.jp/books/9784814400423/) by 小竹 泰一 (O'Reilly Japan, 2023)
- **Official repository:** [oreilly-japan/pentest-starting-with-port-scanner](https://github.com/oreilly-japan/pentest-starting-with-port-scanner)

## Status

Work in progress.

# Port Scanner

A personal project for learning port scanning, networking, and penetration testing.

This project is based on the book and its official sample code listed below, rather than being developed entirely from scratch.

## References

- **Book:** [ポートスキャナ自作ではじめるペネトレーションテスト](https://www.oreilly.co.jp/books/9784814400423/) by 小竹 泰一 (O'Reilly Japan, 2023)
- **Official repository:** [oreilly-japan/pentest-starting-with-port-scanner](https://github.com/oreilly-japan/pentest-starting-with-port-scanner)

## Status

Work in progress.

### Chapter 1: Docker and Lab Environment

- Wrote a Docker Compose configuration for six services: BIND, Nginx, PostgreSQL, SSH, a Log4j test application, and a penetration testing container.
- Configured Docker networking, including static IP and MAC addresses, port mappings, and a custom subnet.
- Validated the Compose configuration using `docker compose config -q`.
- Wrote a Dockerfile based on Ubuntu 22.04 to set up a penetration testing environment.
- Configured system packages, networking tools, a Python 3.11 virtual environment, and a non-root user.
- Practiced Dockerfile instructions, Linux permissions, and package management.

The Dockerfile has been reviewed but has not yet been tested through a complete image build.

### Chapter 2: Python and Network Scanning

- Implemented basic TCP Connect and SYN port scanners using Python sockets and Scapy.
- Learned how TCP connections work, including the three-way handshake, TCP flags, and sequence and acknowledgment numbers.
- Built and sent custom SYN, ACK, and FIN/ACK packets.
- Captured and inspected ICMP packets, including Echo Requests and Echo Replies.
- Analyzed TCP traffic with tcpdump and investigated unexpected RST packets.
- Practiced handling timeouts, missing responses, and unexpected TCP flags.
- Tested the scanners against local services on `127.0.0.1`.

TCP packet transmission and response handling have been tested, but a graceful TCP connection shutdown has not yet been verified.

### Chapter 3: Nmap Automation

Currently learning POSIX shell scripting and preparing to automate Nmap scans using target and exclusion lists.
