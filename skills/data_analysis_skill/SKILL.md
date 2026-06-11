---
name: data_analysis
description: Analyze CSV, JSON, and Excel data with statistics, filtering, aggregation, and visualization
version: 1.0.0
---

# Data Analysis Skill

## Description
Loads and analyzes tabular data from CSV and JSON files. Provides descriptive statistics, column filtering, group-by aggregation, and chart generation. Built on Python stdlib with no heavy dependencies.

## Triggers
- analyze csv
- analyze data
- summarize dataset
- filter data
- aggregate data

## Usage
Use load_csv(path) or load_json(path) to load data, then describe(), filter(column, op, value), aggregate(group_by, agg_col, func), or to_chart(type) for analysis.
