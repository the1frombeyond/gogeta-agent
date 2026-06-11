---
name: docker
description: Docker container and image management: lifecycle, compose, logs, stats, and cleanup
version: 1.0.0
---

# Docker Skill

## Description
Manages Docker containers and images through the Docker CLI. Supports container lifecycle (start/stop), log inspection, image listing, Docker Compose operations, and system pruning.

## Triggers
- docker containers
- start container
- docker logs
- docker compose
- prune docker

## Usage
Use list_containers(all=False), start(name), stop(name), logs(name, lines=50), list_images(), compose_up(file), or prune().
