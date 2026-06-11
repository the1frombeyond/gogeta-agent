---
name: voice
description: High-fidelity neural speech synthesis using Edge-TTS with mood-aware voice selection.
version: 1.2.0
---

# Voice Skill

This skill provides JARVIS with a high-quality neural voice for verbal interaction.

## Instructions
1. Use the `speak` command to convert text to audio.
2. Select the voice based on the current system mood:
   - **Calm/Neutral**: `en-US-AriaNeural`
   - **Alert/Urgent**: `en-US-GuyNeural`
   - **Friendly/Social**: `en-US-JennyNeural`
3. Always adjust the speaking rate based on the `voice_speed` setting in `user_config.json`.

## Engine
- **Edge-TTS**: Used for low-latency, high-quality neural synthesis.
