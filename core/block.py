import hashlib
import json
import time

class Block:
    def __init__(self, index, logs, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.logs = logs  # Lista contendo os objetos LogRecord validados
        self.previous_hash = previous_hash
        # O Hash é calculado instantaneamente na criação do bloco, sem precisar de mineração
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Gera a 'impressão digital' única deste bloco usando SHA-256.
        """
        logs_dict_list = [log.to_dict() for log in self.logs]

        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "logs": logs_dict_list,
            "previous_hash": self.previous_hash
        }

        block_string = json.dumps(block_content, sort_keys=True).encode('utf-8')

        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        """
        Converte o bloco inteiro para um formato amigável.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "logs": [log.to_dict() for log in self.logs],
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }