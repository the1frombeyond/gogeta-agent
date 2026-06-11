---
name: network_tools
description: Network diagnostics: ping, traceroute, DNS lookup, port scanning, and bandwidth testing
version: 1.0.0
---

# Network Tools Skill

## Description
Full suite of network diagnostic tools including ICMP ping, traceroute, DNS resolution, TCP port scanning, and HTTP endpoint checking. Uses subprocess for ping/traceroute and socket for DNS/port operations.

## Triggers
- ping google.com
- dns lookup
- port scan
- check network
- traceroute

## Usage
Use ping(host), traceroute(host), dns_lookup(domain), port_scan(host, ports), or http_check(url) for diagnostics.
