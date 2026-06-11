---
name: voice_id
description: Biometric voice identification system that secures JARVIS by recognizing your unique voice print even in noisy environments.
version: 1.0.0
---

# Voice Identification Skill

This skill allows JARVIS to identify your unique voice and protect the system from unauthorized voice commands.

## Enrollment Workflow
1. **Initiation**: Say "JARVIS, enroll my voice."
2. **Phrases**: JARVIS will ask you to repeat 4 specific phrases.
3. **Modeling**: JARVIS extracts your "Voice Print" (ECAPA-TDNN embedding) and stores it securely in `.mark/voice_profiles/`.

## Continuous Adaptation
Every time you speak to JARVIS and your voice is verified, JARVIS slightly updates your profile. This allows the system to follow natural changes in your voice (morning voice, illness, aging) without needing re-enrollment.

## Robustness
- **Noise Cancellation**: Uses deep learning embeddings that focus on speaker characteristics rather than background frequencies.
- **Crosstalk Filtering**: If multiple people are talking, JARVIS will only execute commands that match your specific voice print score.

## Security
- Your voice print is stored as a non-reversible numerical vector (embedding).
- Commands from unauthorized voices are logged but not executed.
