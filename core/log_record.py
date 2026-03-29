import json
from collections import OrderedDict

class LogRecord:
    def __init__(self, node_public_key, timestamp, namespace, pod_name, level, message, signature=""):
        self.node_public_key = node_public_key 
        self.timestamp = timestamp
        self.namespace = namespace
        self.pod_name = pod_name
        self.level = level
        self.message = message
        self.signature = signature

    def to_dict(self):
        return OrderedDict({
            'node_public_key': self.node_public_key,
            'timestamp': self.timestamp,
            'namespace': self.namespace,
            'pod_name': self.pod_name,
            'level': self.level,
            'message': self.message
        })

    def get_log_string(self):
        # Converte o dicionário em string
        return json.dumps(self.to_dict(), sort_keys=True)

    def is_valid(self):
        # Todo log legítimo tem que ter assinatura
        if not self.signature:
            return False
            
        # Verifica matematicamente se ninguém alterou o texto do log no meio do caminho
        from core.wallet import Wallet
        return Wallet.verify_signature(
            self.node_public_key, 
            self.signature, 
            self.get_log_string()
        )