import os
import time
from dotenv import load_dotenv
from core.block import Block

load_dotenv()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_logs = []
        
        # Regras de Negócio da arquitetura permissionada
        self.max_logs_per_block = 10
        self.delay_block = float(os.getenv("DELAY_BLOCK", "0.0"))
        
        # Ao nascer, a blockchain sempre cria o "Bloco Zero"
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        O Bloco Gênesis é o alicerce. Não contém logs e seu hash anterior é 0.
        """
        genesis_block = Block(index=0, logs=[], previous_hash="0")
        self.chain.append(genesis_block)
        print("[*] Bloco Gênesis gerado e ancorado com sucesso.")

    def get_latest_block(self):
        return self.chain[-1]

    def add_log(self, log_record):
        """
        Tenta adicionar um novo LogRecord à Mempool.
        """
        # Auditoria 
        if not log_record.is_valid():
            print("[X] ALERTA DE SEGURANÇA: Log rejeitado! Assinatura inválida ou conteúdo corrompido.")
            return False
        
        # Entrada na Mempool
        self.pending_logs.append(log_record)
        print(f"[OK] Log validado. Mempool: {len(self.pending_logs)}/{self.max_logs_per_block}")

        # Gatilho de Selagem
        if len(self.pending_logs) >= self.max_logs_per_block:
            self.seal_block()
        
        return True

    def seal_block(self):
        """
        Pega os 10 logs da Mempool e sela matematicamente em um novo bloco.
        """
        print("\n[*] Capacidade máxima atingida. Iniciando empacotamento...")
        
        # Pausa para acompanhar no Dashboard
        if self.delay_block > 0:
            print(f"[*] Modo Auditoria: Pausando {self.delay_block} segundos para o consenso visual...")
            time.sleep(self.delay_block)

        latest_block = self.get_latest_block()
        
        # Criando o bloco passando os primeiros 10 logs da fila
        logs_to_seal = self.pending_logs[:self.max_logs_per_block]
        
        new_block = Block(
            index=latest_block.index + 1,
            logs=logs_to_seal,
            previous_hash=latest_block.hash
        )
        
        # Atualizando a Corrente Oficial
        self.chain.append(new_block)
        
        # Limpando apenas os 10 logs que foram empacotados
        self.pending_logs = self.pending_logs[self.max_logs_per_block:]
        
        print(f"[Cadeado] Bloco {new_block.index} selado! Hash SHA-256: {new_block.hash[:20]}...\n")
        return new_block