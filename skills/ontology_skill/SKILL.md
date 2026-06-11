---
name: ontology
description: Knowledge representation system for storing verifiable information as an entity-relation graph with strict type validation.
version: 1.0.0
---

# Ontology Skill

This skill allows JARVIS to represent complex knowledge about people, projects, tasks, and events as a verifiable graph.

## Core Concepts
- **Entity**: An object with a type and properties (e.g., Task, Person).
- **Relation**: A link between two entities (e.g., Project -> has_owner -> Person).
- **Validation**: Every change is checked against `schema.yaml` for type correctness.

## Instructions
1. Use `create` to add new entities (Person, Project, Task).
2. Use `relate` to link entities together.
3. Use `query` to search the graph.
4. **Append-Only**: Always append to `graph.jsonl` to preserve history.

## Storage
- `.mark/memory/ontology/graph.jsonl`: The verifiable action log.
- `.mark/memory/ontology/schema.yaml`: The type constraint system.

## Example Workflows
- "Remember that Tony is the owner of the JARVIS project."
- "What tasks are blocked by the database migration?"
