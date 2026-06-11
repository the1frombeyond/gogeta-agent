---
name: weather
description: Current weather, 7-day forecasts, and severe weather alerts for any global location
version: 1.0.0
---

# Weather Skill

## Description
Retrieves current weather conditions, multi-day forecasts, and severe weather alerts for any location worldwide. Uses the free Open-Meteo API (no API key required).

## Triggers
- what's the weather
- weather forecast
- weather in london
- storm alerts

## Usage
Provide a location string. Use get_current(location) for current conditions, get_forecast(location, days=7) for extended forecast, and get_alerts(region) for severe weather warnings.
