---
name: media
description: Image, audio, and video processing: metadata reading, format conversion, thumbnails, and basic editing
version: 1.0.0
---

# Media Skill

## Description
Processes image, audio, and video files. Reads metadata, converts between formats, and extracts basic information. Uses Pillow for image operations when available.

## Triggers
- image info
- convert image
- video metadata
- audio info
- get media info

## Usage
Use image_info(path), convert_image(src, dst, format), video_info(path), or audio_info(path) to inspect and convert media files.
