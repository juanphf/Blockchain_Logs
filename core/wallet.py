import binascii
from ecdsa import SigningKey, VerifyingKey, NIST256p

class Wallet:
    def __init__(self):
        # Gerando par de chaves
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()

    @property
    def public_key(self):
        # Converte a chave publica para hexadecimal para poder enviar pelo Kafka em formato JSON.
        return binascii.hexlify(self._public_key.to_string()).decode('ascii')

    def sign_log(self, log_string):
        # Pega o texto do log e carimba usando sua chave privada.
        signature = self._private_key.sign(log_string.encode('utf-8'))
        # Retorna a assinatura matemática única para aquele texto específico.
        return binascii.hexlify(signature).decode('ascii')

    # A Função de Auditoria é estática porque qualquer Nó pode chamar sem precisar instanciar a carteira de quem enviou.
    @staticmethod
    def verify_signature(public_key_hex, signature_hex, log_string):
        try:
            # Desfaz a conversão de texto de volta para bytes
            public_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            
            # Recria o objeto da Chave Pública a partir dos bytes recebidos
            verifying_key = VerifyingKey.from_string(public_key_bytes, curve=NIST256p)
            
            # Verifica se a assinatura bate com a chave e com o texto
            return verifying_key.verify(signature_bytes, log_string.encode('utf-8'))
        
        except Exception:
            # Se der qualquer erro a biblioteca ECDSA lança uma exceção.
            return False