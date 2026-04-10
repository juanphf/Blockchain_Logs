import os
import time
from dotenv import load_dotenv
from core.block import Block
from core.log_record import LogRecord
from core.wallet import Wallet

load_dotenv()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_logs = []
        
        # Identidade deste nó na rede
        self.node_wallet = Wallet()
        print(f"[*] Identidade do Nó Criada (Public Key): {self.node_wallet.public_key[:20]}...")
        
        self.max_logs_per_block = 10
        self.delay_block = float(os.getenv("DELAY_BLOCK", "0.0"))
        
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        O Bloco Gênesis é o alicerce. Ele DEVE ser matematicamente idêntico 
        em todos os nós do planeta. Por isso, travamos o timestamp em 0.0.
        """
        genesis_block = Block(index=0, logs=[], previous_hash="0", timestamp=0.0)
        self.chain.append(genesis_block)
        print(f"[*] Bloco Gênesis ancorado. Hash Oficial: {genesis_block.hash[:15]}...")

    def get_latest_block(self):
        return self.chain[-1]

    def add_log(self, log_data):
        """Adiciona log validado à Mempool local."""
        try:
            log_record = LogRecord.from_dict(log_data)
        except KeyError as e:
            return None

        if not log_record.is_valid():
            return None
            
        # Evita logs duplicados na mempool
        if any(l.signature == log_record.signature for l in self.pending_logs):
            return None

        self.pending_logs.append(log_record)
        print(f"[OK] Log na Mempool: {len(self.pending_logs)}/{self.max_logs_per_block}")

        if len(self.pending_logs) >= self.max_logs_per_block:
            return self.seal_block() # Retorna o bloco recém criado
        return None
    
    def seal_block(self):
        """O Nó atinge a cota, cria e assina o bloco como PROPOSTA."""
        print("\n[*] Empacotando bloco e assinando...")
        if self.delay_block > 0:
            time.sleep(self.delay_block)

        latest_block = self.get_latest_block()
        logs_to_seal = self.pending_logs[:self.max_logs_per_block]
        
        new_block = Block(
            index=latest_block.index + 1,
            logs=logs_to_seal,
            previous_hash=latest_block.hash
        )
        
        # Assina o bloco com a identidade deste Nó
        new_block.sign_block(self.node_wallet)
        
        # Limpa os logs que foram empacotados da mempool
        self.pending_logs = self.pending_logs[self.max_logs_per_block:]
        
        print(f"[*] Bloco {new_block.index} PROPOSTO por mim! Aguardando ordem do Kafka. Hash: {new_block.hash[:15]}...\n")
        
        return new_block # Retorna para o API.py publicar no Kafka

    def add_proposed_block(self, block_data):
        """Acionado quando um bloco de QUALQUER NÓ chega via Kafka."""
        try:
            proposed_block = Block.from_dict(block_data)
        except Exception as e:
            return False

        latest_block = self.get_latest_block()

        if proposed_block.index < latest_block.index:
            print(f"\n[!!!] ALERTA CRÍTICO: Tentativa de reescrever a história! O Bloco {proposed_block.index} já está consolidado. Ataque bloqueado!")
            return False

        if proposed_block.index == latest_block.index:
            print(f"[!] Bloco {proposed_block.index} (Hash: {proposed_block.hash[:8]}...) descartado. A rede já aceitou um bloco mais rápido!")
            return False
            
        # Verificação de encaixe: Se não for exatamente o próximo, rejeita silenciosamente
        if proposed_block.index != latest_block.index + 1 or proposed_block.previous_hash != latest_block.hash:
            return False

        # Validação matemática e de Whitelist
        if not proposed_block.is_valid_block():
            print(f"[X] Bloco {proposed_block.index} recebido da rede é inválido!")
            return False

        self.chain.append(proposed_block)
        print(f"[Consenso] Bloco {proposed_block.index} ancorado com sucesso! Hash: {proposed_block.hash[:15]}...")
        
        # Limpa da nossa Mempool local os logs que já vieram dentro deste bloco vencedor
        signatures_in_block = [log.signature for log in proposed_block.logs]
        self.pending_logs = [log for log in self.pending_logs if log.signature not in signatures_in_block]
        return True

    def replace_chain(self, external_chain_dicts):
        """Mecanismo de Sincronização. Substitui cadeia se a externa for maior e válida."""
        try:
            external_chain = [Block.from_dict(b) for b in external_chain_dicts]
            
            # Verifica se a cadeia externa é de fato maior
            if len(external_chain) <= len(self.chain):
                return False

            # Valida toda a cadeia externa
            for i in range(1, len(external_chain)):
                current = external_chain[i]
                previous = external_chain[i-1]
                
                if current.previous_hash != previous.hash or not current.is_valid_block():
                    print(f"[X] Tentativa de sincronização falhou: Bloco {current.index} corrompido.")
                    return False

            # Se chegou aqui, a nova cadeia é confiável e maior
            self.chain = external_chain
            print(f"[*] Sincronização concluída! Cadeia atualizada para {len(self.chain)} blocos.")
            return True
            
        except Exception as e:
            # AGORA ELE VAI GRITAR O ERRO NA TELA EM VEZ DE ESCONDER
            print(f"\n[X] Erro crítico no Sincronismo da Cadeia: {e}")
            import traceback
            traceback.print_exc()
            return False