import os
import random
import time
import json
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from confluent_kafka import Producer

from core.wallet import Wallet
from core.log_record import LogRecord
from network.config import get_producer_config, TOPIC_LOGS

load_dotenv()

class K8sLogGenerator:
    def __init__(self, seed_value=None):
        if seed_value is not None:
            random.seed(seed_value)
            print(f"[*] Gerador inicializado com a semente (seed): {seed_value}")
        else:
            print("[*] Gerador inicializado de forma totalmente aleatória.")

        self.namespaces = ["production", "staging", "kube-system", "monitoring"]
        self.apps = ["auth-service", "payment-gateway", "nginx-ingress", "postgres-db", "frontend-app"]
        self.levels = ["INFO"] * 60 + ["WARNING"] * 25 + ["ERROR"] * 10 + ["CRITICAL"] * 5

        self.messages = {
            "INFO": ["Container started", "Readiness probe passed", "Liveness probe passed", "HTTP GET /health 200 OK"],
            "WARNING": ["High memory usage detected (85%)", "Connection timeout retrying...", "CPU throttling active"],
            "ERROR": ["Failed to connect to postgres-db", "Timeout waiting for response", "Permission denied on /etc/secrets"],
            "CRITICAL": ["Pod CrashLoopBackOff", "OOMKilled (Out of Memory)", "Volume mount failed - Disk full"]
        }

        self.wallet = Wallet()
        self.public_key = self.wallet.public_key
        self.producer = Producer(get_producer_config())

    def delivery_report(self, err, msg):
        """Callback acionado pelo Kafka APÓS tentar entregar a mensagem."""
        if err is not None:
            print(f"[!!!] ERRO DE REDE: Falha ao entregar ao Kafka: {err}")
        else:
            log_data = json.loads(msg.value().decode('utf-8'))
            print(f"[>] CONFIRMADO no Kafka: [{log_data['level']}] {log_data['pod_name']}")

    def generate_log(self):
        app = random.choice(self.apps)
        pod_hash = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
        pod_name = f"{app}-{pod_hash}"
        level = random.choice(self.levels)
        message = random.choice(self.messages[level])

        log_record = LogRecord(
            node_public_key=self.public_key,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            namespace=random.choice(self.namespaces),
            pod_name=pod_name,
            level=level,
            message=message
        )

        log_string = log_record.get_log_string()
        log_record.signature = self.wallet.sign_message(log_string)

        final_dict = log_record.to_dict()
        final_dict["signature"] = log_record.signature
        return final_dict

    def send_to_kafka(self, log_dict):
        self.producer.produce(
            TOPIC_LOGS, 
            value=json.dumps(log_dict).encode('utf-8'),
            callback=self.delivery_report
        )
        self.producer.poll(0)

if __name__ == "__main__":
    semente_do_trabalho = int(os.getenv("LOG_SEED", "20260406"))
    delay_log = float(os.getenv("DELAY_LOG", "2.0"))
    
    gerador = K8sLogGenerator(seed_value=semente_do_trabalho)

    print(f"\n[*] Iniciando simulação do Cluster K8s (Delay: {delay_log}s) ...")
    print(f"[*] Enviando para o tópico: {TOPIC_LOGS}")
    
    try:
        while True:
            novo_log = gerador.generate_log()
            gerador.send_to_kafka(novo_log)
            
            if delay_log > 0:
                time.sleep(delay_log)
                
    except KeyboardInterrupt:
        print("\n[*] Interrupção solicitada. Aguardando confirmação final do Kafka...")
        try:
            gerador.producer.flush(timeout=3.0) 
        except Exception:
            pass
        sys.exit(0)