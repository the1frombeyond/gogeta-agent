---
name: system_monitor
description: Real-time system monitoring: CPU, RAM, disk, network, process tracking, and performance alerts
version: 1.0.0
---

# System Monitor Skill

## Description
Monitors system resources in real-time including CPU usage, memory consumption, disk space, network I/O, and running processes. Powered by psutil with graceful fallbacks.

## Triggers
- system status
- check cpu usage
- memory usage
- running processes
- top processes

## Usage
Call get_cpu(), get_memory(), get_disk(), get_network(), list_processes(), or get_top_processes(n) to retrieve system metrics.
