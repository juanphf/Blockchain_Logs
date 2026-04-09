import json
import requests
import time
from confluent_kafka import Producer
from network.config import get_producer_config, TOPIC_BLOCKS, NODE_API_URL
from core.wallet import Wallet
from core.block import Block

def simulate_history_rewrite():
    print("[!] Iniciando Simulação de Ataque 2: Adulteração do Passado")
    producer = Producer(get_producer_config())
    
    # 1. O atacante rouba a corrente atual baixando da API de um nó
    print(f"[*] Baixando a blockchain do nó alvo ({NODE_API_URL})...")
    try:
        chain_data = requests.get(f"{NODE_API_URL}/blocks").json()
    except Exception as e:
        print("[X] Erro ao conectar no nó. Ele está rodando?")
        return

    if len(chain_data) < 3:
        print("[X] A rede precisa ter pelo menos 3 blocos para simular adulteração do passado.")
        return

    # 2. O Atacante escolhe qual bloco quer atacar
    # Você pode colocar um número fixo (ex: alvo_index = 19)
    # Ou usar -2 para atacar sempre o "penúltimo" bloco da rede
    alvo_index = len(chain_data) - 2 

    if alvo_index <= 0:
        print("[X] A rede ainda não tem blocos suficientes para atacar o passado.")
        return

    target_block = chain_data[alvo_index]
    print(f"[*] Bloco Alvo capturado: Index {target_block['index']}, Hash Original: {target_block['hash'][:15]}...")

    
    # 3. O ATAQUE: Modificando os dados dentro do bloco passado
    print("[*] Envenenando o log dentro do Bloco 1...")
    target_block['logs'][0]['message'] = "HACKER_TRANSFERIU_1_MILHAO_DE_DOLARES"

    # 4. O atacante usa sua própria carteira (simulando que roubou a chave de um nó) para reassinar
    hacker_wallet = Wallet()
    
    # Recria o objeto Block para recalcular a matemática do bloco envenenado
    poisoned_block = Block.from_dict(target_block)
    # Recalcula o Hash com a nova mensagem falsa
    poisoned_block.hash = poisoned_block.calculate_hash()
    # O Hacker assina o novo bloco para parecer legítimo
    poisoned_block.sign_block(hacker_wallet)

    print(f"[*] Bloco adulterado reassinado! Novo Hash Falso: {poisoned_block.hash[:15]}...")
    print(f"[*] Transmitindo bloco do passado envenenado para a rede Kafka no tópico '{TOPIC_BLOCKS}'...")

    # O atacante usa a chave de consenso tentando forçar a rede a aceitar
    producer.produce(
        TOPIC_BLOCKS, 
        key="consensus", 
        value=json.dumps(poisoned_block.to_dict()).encode('utf-8')
    )
    producer.flush()
    print("[!] Ataque enviado! Verifique a reação da rede.")

if __name__ == "__main__":
    simulate_history_rewrite()