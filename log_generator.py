import os
import random
import time
import json
from datetime import datetime
from dotenv import load_dotenv

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

    def generate_log(self):
        app = random.choice(self.apps)
        pod_hash = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
        pod_name = f"{app}-{pod_hash}"
        level = random.choice(self.levels)
        message = random.choice(self.messages[level])

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "namespace": random.choice(self.namespaces),
            "pod_name": pod_name,
            "level": level,
            "message": message
        }

# --- BLOCO DE EXECUÇÃO ---
if __name__ == "__main__":
    semente_do_trabalho = int(os.getenv("LOG_SEED", "20260406"))
    delay_log = float(os.getenv("DELAY_LOG", "0.5"))
    
    gerador = K8sLogGenerator(seed_value=semente_do_trabalho)

    print(f"\n[*] Iniciando simulação do Cluster K8s (Delay: {delay_log}s) ...")
    print("[*] Pressione Ctrl+C para parar.\n")
    
    try:
        while True:
            novo_log = gerador.generate_log()
            print(json.dumps(novo_log, indent=2))
            
            if delay_log > 0:
                time.sleep(delay_log)
    except KeyboardInterrupt:
        print("\n[*] Geração de logs interrompida com sucesso.")