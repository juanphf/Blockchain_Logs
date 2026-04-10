import hashlib
import json
import time
from core.log_record import LogRecord
from network.config import ALLOWED_NODES

class Block:
    def __init__(self, index, logs, previous_hash, timestamp=None, miner_pub_key="", signature="", hash_val=""):
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.logs = logs  # Lista de objetos LogRecord
        self.previous_hash = previous_hash
        self.miner_pub_key = miner_pub_key
        self.signature = signature
        # Se veio pela rede, usa o hash recebido. Se foi recém criado, calcula.
        self.hash = hash_val or self.calculate_hash()

    def calculate_hash(self):
        logs_dict_list = [log.to_dict() for log in self.logs]
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "logs": logs_dict_list,
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(block_content, sort_keys=True).encode('utf-8')
        return hashlib.sha256(block_string).hexdigest()

    def sign_block(self, node_wallet):
        """O nó que empacotou o bloco deixa sua assinatura matemática."""
        self.miner_pub_key = node_wallet.public_key
        # O minerador assina o Hash do bloco
        self.signature = node_wallet.sign_message(self.hash)

    def is_valid_block(self):
        """Auditoria completa do bloco recebido (Com Debug)"""
        # Verifica se o hash confere com o conteúdo
        if self.hash != self.calculate_hash():
            print(f"\n[DEBUG] Falha 1: O Hash calculado é diferente do recebido!")
            print(f"-> Recebido:  {self.hash}")
            print(f"-> Calculado: {self.calculate_hash()}\n")
            return False
            
        # Ignora o Gênesis
        if self.index == 0:
            return True 
            
        # Verifica Whitelist do Minerador
        from network.config import ALLOWED_NODES
        if ALLOWED_NODES and self.miner_pub_key not in ALLOWED_NODES:
            print("[DEBUG] Falha 3: Bloco rejeitado porque o Minerador não está na Whitelist.")
            return False
            
        # Verifica a Assinatura do Minerador
        from core.wallet import Wallet
        if not Wallet.verify_signature(self.miner_pub_key, self.signature, self.hash):
            print("[DEBUG] Falha 4: A Assinatura criptográfica do bloco é inválida.")
            return False
            
        # Verifica todos os logs dentro do bloco
        for i, log in enumerate(self.logs):
            if not log.is_valid():
                print(f"[DEBUG] Falha 5: O Log número {i+1} dentro do bloco corrompeu a validação.")
                return False
                
        return True

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "logs": [log.to_dict() for log in self.logs],
            "previous_hash": self.previous_hash,
            "miner_pub_key": self.miner_pub_key,
            "signature": self.signature,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, data):
        logs = [LogRecord.from_dict(log_data) for log_data in data['logs']]
        return cls(
            index=data['index'],
            logs=logs,
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            miner_pub_key=data.get('miner_pub_key', ''),
            signature=data.get('signature', ''),
            hash_val=data['hash']
        )