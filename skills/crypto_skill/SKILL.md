---
name: cryptography
description: Hash, encrypt, decrypt, sign, and verify data with multiple algorithms
version: 1.0.0
---

# Cryptography

## Description
Cryptographic tools for hashing, encryption, decryption, signing, and verification using multiple algorithms.

## Triggers
- hash text
- encrypt file
- decrypt data
- sign message
- verify signature
- crypto

## Usage
- `hash(text, algorithm)` — Hash text with sha256/md5/sha512
- `encrypt(text, key)` — Simple AES-like encryption
- `decrypt(ciphertext, key)` — Decrypt data
- `sign(text, private_key)` — Generate signature
- `verify(text, signature, public_key)` — Verify signature
