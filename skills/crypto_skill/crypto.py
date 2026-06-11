import base64
import hashlib


class Crypto:
    def hash(self, text, algorithm="sha256"):
        h = hashlib.new(algorithm, text.encode())
        return h.hexdigest()

    def encrypt(self, text, key):
        xored = bytes(a ^ ord(key[i % len(key)]) for i, a in enumerate(text.encode()))
        return base64.b64encode(xored).decode()

    def decrypt(self, ciphertext, key):
        raw = base64.b64decode(ciphertext.encode())
        plain = bytes(a ^ ord(key[i % len(key)]) for i, a in enumerate(raw))
        return plain.decode()

    def sign(self, text, private_key):
        return hashlib.sha256((text + private_key).encode()).hexdigest()

    def verify(self, text, signature, public_key):
        return hashlib.sha256((text + public_key).encode()).hexdigest() == signature


def run(action, **kwargs):
    c = Crypto()
    return getattr(c, action)(**kwargs)
