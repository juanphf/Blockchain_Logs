import random
import time
import json
from datetime import datetime

class K8sLogGenerator:
    def __init__(self, seed_value=None):
        if seed_value is not None:
            random.seed(seed_value)
            print(f"[*] Gerador inicializado com a semente (seed): {seed_value}")
        else:
            print("[*] Gerador inicializado de forma totalmente aleatória.")

        # Dicionários de dados falsos para simular um Cluster K8s real
        self.namespaces = ["production", "staging", "kube-system", "monitoring"]
        self.apps = ["auth-service", "payment-gateway", "nginx-ingress", "postgres-db", "frontend-app"]
        
        # Pesos para níveis de log (INFO acontece muito mais que CRITICAL)
        self.levels = ["INFO"] * 60 + ["WARNING"] * 25 + ["ERROR"] * 10 + ["CRITICAL"] * 5

        self.messages = {
            "INFO": ["Container started", "Readiness probe passed", "Liveness probe passed", "HTTP GET /health 200 OK"],
            "WARNING": ["High memory usage detected (85%)", "Connection timeout retrying...", "CPU throttling active"],
            "ERROR": ["Failed to connect to postgres-db", "Timeout waiting for response", "Permission denied on /etc/secrets"],
            "CRITICAL": ["Pod CrashLoopBackOff", "OOMKilled (Out of Memory)", "Volume mount failed - Disk full"]
        }

    def generate_log(self):
        # Escolhe aleatoriamente os componentes
        app = random.choice(self.apps)
        pod_hash = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
        pod_name = f"{app}-{pod_hash}"
        
        level = random.choice(self.levels)
        message = random.choice(self.messages[level])

        # Monta a estrutura final do Log (A sua "Transação")
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "namespace": random.choice(self.namespaces),
            "pod_name": pod_name,
            "level": level,
            "message": message
        }
        
        return log_entry

# --- BLOCO DE EXECUÇÃO ---
if __name__ == "__main__":
    # Usamos uma semente fixa para obter os MESMOS logs
    semente_do_trabalho = 20260406
    
    gerador = K8sLogGenerator(seed_value=semente_do_trabalho)

    print("\n--- Gerando 5 Logs do Kubernetes ---")
    for i in range(5):
        novo_log = gerador.generate_log()
        # Imprime o JSON
        print(json.dumps(novo_log, indent=2))
        
        # Pausa um pouquinho para simular tempo real
        time.sleep(0.5)