import binascii
from ecdsa import SigningKey, VerifyingKey, NIST256p

class Wallet:
    def __init__(self):
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()

    @property
    def public_key(self):
        return binascii.hexlify(self._public_key.to_string()).decode('ascii')

    def sign_message(self, message_string):
        """Assina qualquer string genérica (logs ou hashes de blocos)"""
        signature = self._private_key.sign(message_string.encode('utf-8'))
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_signature(public_key_hex, signature_hex, message_string):
        try:
            public_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            verifying_key = VerifyingKey.from_string(public_key_bytes, curve=NIST256p)
            return verifying_key.verify(signature_bytes, message_string.encode('utf-8'))
        except Exception:
            return False