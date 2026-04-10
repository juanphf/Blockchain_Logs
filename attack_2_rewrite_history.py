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
    
    print(f"[*] Baixando a blockchain do nó alvo ({NODE_API_URL})...")
    try:
        chain_data = requests.get(f"{NODE_API_URL}/blocks").json()
    except Exception as e:
        print("[X] Erro ao conectar no nó. Ele está rodando?")
        return

    if len(chain_data) < 3:
        print("[X] A rede precisa ter pelo menos 3 blocos para simular adulteração do passado.")
        return

    # usar -2 para atacar sempre o "penúltimo" bloco da rede
    alvo_index = len(chain_data) - 2 

    if alvo_index <= 0:
        print("[X] A rede ainda não tem blocos suficientes para atacar o passado.")
        return

    target_block = chain_data[alvo_index]
    print(f"[*] Bloco Alvo capturado: Index {target_block['index']}, Hash Original: {target_block['hash'][:15]}...")


    print("[*] Envenenando o log dentro do Bloco 1...")
    target_block['logs'][0]['message'] = "HACKER_TRANSFERIU_1_MILHAO_DE_DOLARES"

    hacker_wallet = Wallet()
    
    poisoned_block = Block.from_dict(target_block)
    poisoned_block.hash = poisoned_block.calculate_hash()
    poisoned_block.sign_block(hacker_wallet)

    print(f"[*] Bloco adulterado reassinado! Novo Hash Falso: {poisoned_block.hash[:15]}...")
    print(f"[*] Transmitindo bloco do passado envenenado para a rede Kafka no tópico '{TOPIC_BLOCKS}'...")

    producer.produce(
        TOPIC_BLOCKS, 
        key="consensus", 
        value=json.dumps(poisoned_block.to_dict()).encode('utf-8')
    )
    producer.flush()
    print("[!] Ataque enviado! Verifique a reação da rede.")

if __name__ == "__main__":
    simulate_history_rewrite()