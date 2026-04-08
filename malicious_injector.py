import json
import time
from confluent_kafka import Producer
from network.config import get_producer_config, TOPIC_LOGS

def inject_malicious_log():
    # Inicializando do produtor nativo, como se fosse um client TCP puro espetando no Kafka
    producer = Producer(get_producer_config())
    
    # Payload forjado: Estrutura idêntica, informações falsas, e mais crítico: chaves/assinaturas não-criptografadas!
    fake_log = {
        "node_public_key": "HACKER_FAKE_PUBLIC_KEY_XXX_999",
        "timestamp": time.time(),
        "namespace": "kube-system",
        "pod_name": "hacker-terminal-0",
        "level": "CRITICAL",
        "message": "DROP TABLE logs; -- INJEÇÃO ESTRAPOLADORA ENVIADA",
        "signature": "SIGNATURE_INVÁLIDA_TENTANDO_ENGANAR_A_REDE"
    }

    print("====================================")
    print("⚠  INICIANDO INJEÇÃO MALICIOSA...")
    print("====================================")
    print(f"[*] Alvo: Tópico Kafka [{TOPIC_LOGS}]")
    print(f"[*] Carga: \n{json.dumps(fake_log, indent=2)}")
    
    # Disparando para a rede... sem validação
    producer.produce(
        TOPIC_LOGS, 
        value=json.dumps(fake_log).encode('utf-8')
    )
    
    # Garante o envio TCP
    producer.flush()
    print("\n[+] Míssil disparado com sucesso direto no barramento do Kafka!")
    print("[!] Observe os terminais dos Nós da Blockchain. Eles deverão rejeitar liminarmente sem travar a rede.")

if __name__ == "__main__":
    inject_malicious_log()
