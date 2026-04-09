import json
from collections import OrderedDict
from network.config import ALLOWED_NODES

class LogRecord:
    def __init__(self, node_public_key, timestamp, namespace, pod_name, level, message, signature=""):
        self.node_public_key = node_public_key 
        self.timestamp = timestamp
        self.namespace = namespace
        self.pod_name = pod_name
        self.level = level
        self.message = message
        self.signature = signature

    def to_dict(self, include_signature=True):
        data = OrderedDict({
            'node_public_key': self.node_public_key,
            'timestamp': self.timestamp,
            'namespace': self.namespace,
            'pod_name': self.pod_name,
            'level': self.level,
            'message': self.message
        })
        
        # Se a assinatura existir e for solicitada, incluímos no pacote!
        if include_signature and self.signature:
            data['signature'] = self.signature
            
        return data

    def get_log_string(self):
        # A criptografia matemática só pode assinar os DADOS PUROS (sem o campo signature)
        pure_data = self.to_dict(include_signature=False)
        return json.dumps(pure_data, sort_keys=True)

    def is_valid(self):
        # 1. Validação de Identidade (Whitelist)
        from network.config import ALLOWED_NODES
        if ALLOWED_NODES and self.node_public_key not in ALLOWED_NODES:
            print("\n[X] ACESSO NEGADO: Nó remetente não está na Whitelist.")
            return False

        # 2. Validação de Assinatura
        if not self.signature:
            print("\n[X] ALERTA: Tentativa de injeção de log sem assinatura digital.")
            return False
            
        from core.wallet import Wallet
        is_crypto_valid = Wallet.verify_signature(
            self.node_public_key, 
            self.signature, 
            self.get_log_string()
        )
        
        # 3. O Alarme de Adulteração
        if not is_crypto_valid:
            print(f"\n[!!!] INVASÃO DETECTADA: O log do pod '{self.pod_name}' foi adulterado após a assinatura!")
            
        return is_crypto_valid

    @classmethod
    def from_dict(cls, data):
        return cls(
            node_public_key=data['node_public_key'],
            timestamp=data['timestamp'],
            namespace=data['namespace'],
            pod_name=data['pod_name'],
            level=data['level'],
            message=data['message'],
            signature=data.get('signature', '')
        )