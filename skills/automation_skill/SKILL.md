---
name: automation
description: Schedule and manage automated tasks, cron-style jobs, and recurring workflows with persistence
version: 1.0.0
---

# Automation Skill

## Description
Schedules and manages recurring tasks with persistent JSON storage. Supports creating, listing, pausing, resuming, and removing scheduled jobs with configurable intervals.

## Triggers
- schedule task
- automation
- run every hour
- list scheduled tasks
- cron job

## Usage
Use schedule(name, command, interval_minutes), list(), remove(name), pause(name), resume(name), or status() to manage automated tasks. Tasks persist at ~/.jarvis/automation/tasks.json.
