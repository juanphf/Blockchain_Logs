import json
import time
from collections import OrderedDict
from confluent_kafka import Producer
from core.wallet import Wallet
from network.config import get_producer_config, TOPIC_LOGS

def simulate_log_attack():
    print("[!] Iniciando Simulação de Ataque 1: Injeção de Log Falso")
    producer = Producer(get_producer_config())
    
    hacker_wallet = Wallet()
    print(f"[*] Chave Pública do Atacante gerada: {hacker_wallet.public_key[:20]}...")

    fake_log_data = OrderedDict({
        'node_public_key': hacker_wallet.public_key,
        'timestamp': time.time(),
        'namespace': 'kube-system',
        'pod_name': 'auth-service',
        'level': 'CRITICAL',
        'message': 'Acesso ROOT concedido ao usuario hacker_anonimo'
    })

    log_string = json.dumps(fake_log_data, sort_keys=True)
    signature = hacker_wallet.sign_message(log_string)
    
    fake_log_data['message'] = 'DELETAR BANCO DE DADOS PRINCIPAL'
    fake_log_data['signature'] = signature # Anexa a assinatura original

    print(f"[*] Enviando log malicioso envenenado para o tópico '{TOPIC_LOGS}'...")
    
    producer.produce(TOPIC_LOGS, value=json.dumps(fake_log_data).encode('utf-8'))
    producer.flush()
    print("[!] Ataque enviado! Verifique o terminal dos seus Nós.")

if __name__ == "__main__":
    simulate_log_attack()