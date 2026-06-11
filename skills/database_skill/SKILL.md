---
name: database
description: SQLite database management: query, create tables, insert, update, delete, export to CSV/JSON
version: 1.0.0
---

# Database Skill

## Description
Full SQLite database management with table creation, CRUD operations, and data export. Supports parameterized queries for safety and can export tables to CSV or JSON format.

## Triggers
- query database
- create table
- insert into
- export to csv
- run sql

## Usage
Use connect(path), query(sql, params=None), create_table(name, columns), insert(table, data), update(table, data, where), delete(table, where), export_csv(table, path), or export_json(table, path).
